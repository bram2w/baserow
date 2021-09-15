from django.db.models import Q
from django.utils import timezone

from rest_framework.request import Request

from baserow.core.utils import random_string
from baserow.contrib.database.models import Database, Table
from baserow.contrib.database.exceptions import DatabaseDoesNotBelongToGroup
from baserow.contrib.database.table.exceptions import TableDoesNotBelongToGroup

from .exceptions import (
    TokenDoesNotExist,
    MaximumUniqueTokenTriesError,
    TokenDoesNotBelongToUser,
    NoPermissionToTable,
)
from .models import Token, TokenPermission


class TokenHandler:
    def get_by_key(self, key):
        """
        Fetches a single token instance based on the key.

        :param key: The unique token key.
        :param key: str
        :raises TokenDoesNotExist: Raised when the requested token was not found or
            if it does not belong to the user.
        :return: The fetched token matching the provided key.
        :rtype: Token
        """

        try:
            token = Token.objects.select_related("group").get(key=key)
        except Token.DoesNotExist:
            raise TokenDoesNotExist(f"The token with key {key} does not exist.")

        return token

    def get_token(self, user, token_id, base_queryset=None):
        """
        Fetches a single token and checks if the user belongs to the group.

        :param user: The user on whose behalf the token is requested.
        :type user: User
        :param token_id: The id of the requested token.
        :type token_id: int
        :param base_queryset: The base queryset from where to select the token
            object from. This can for example be used to do a `select_related`.
        :type base_queryset: Queryset
        :raises TokenDoesNotExist: Raised when the requested token was not found or
            if it does not belong to the user.
        :return: The fetched token.
        :rtype: Token
        """

        if base_queryset is None:
            base_queryset = Token.objects

        try:
            token = base_queryset.select_related("group").get(id=token_id, user=user)
        except Token.DoesNotExist:
            raise TokenDoesNotExist(f"The token with id {token_id} does not exist.")

        group = token.group
        group.has_user(user, raise_error=True)

        return token

    def generate_unique_key(self, length=32, max_tries=1000):
        """
        Generates a unique token key.

        :param length: Indicates the amount of characters that the token must contain.
        :type length: int
        :param max_tries: The maximum amount of tries to check if a token with the key
            already exists.
        :type max_tries: int
        :raises MaximumUniqueTokenTriesError: When the maximum amount of tries has
            been exceeded. A new generated token is tried every time the token
            already exists.
        :return: A unique token
        :rtype: str
        """

        i = 0

        while True:
            if i > max_tries:
                raise MaximumUniqueTokenTriesError(
                    f"Tried {max_tries} tokens, but none of them are unique."
                )

            i += 1
            token = random_string(length)

            if not Token.objects.filter(key=token).exists():
                return token

    def create_token(self, user, group, name):
        """
        Creates a new API token.

        :param user: The user of whose behalf the token is created.
        :type user: User
        :param group: The group object of which the token is related to.
        :type group: Group
        :param name: The name of the token.
        :type name: str
        :return: The created token instance.
        :rtype: Token
        """

        group.has_user(user, raise_error=True)

        token = Token.objects.create(
            name=name, key=self.generate_unique_key(), user=user, group=group
        )

        # The newly created token should have access to all the tables in the group
        # when it is created.
        self.update_token_permissions(
            user, token, create=True, read=True, update=True, delete=True
        )

        return token

    def rotate_token_key(self, user, token):
        """
        Generates a new key for the provided token object and updates it.

        :param user: The user on whose behalf the key is refreshed.
        :type user: User
        :param token: The token instance of which the key needs to be refreshed.
        :type token: Token
        :raises TokenDoesNotBelongToUser: When the provided token does not belong the
            provided user.
        :return: The updated token instance.
        :rtype: Token
        """

        if not user.id == token.user_id:
            raise TokenDoesNotBelongToUser(
                "The user is not authorized to rotate the " "key."
            )

        token.key = self.generate_unique_key()
        token.save()

        return token

    def update_token(self, user, token, name):
        """
        Updates an existing token.

        :param user: The user on whose behalf the token is updated.
        :type user: User
        :param token: The token object that needs to be updated.
        :type token: Token
        :param name: The new name of the token.
        :type name: str
        :raises TokenDoesNotBelongToUser: When the provided token does not belong the
            provided user.
        :return: The updated token instance.
        :rtype: Token
        """

        if not user.id == token.user_id:
            raise TokenDoesNotBelongToUser(
                "The user is not authorized to rotate the " "key."
            )

        token.name = name
        token.save()

        return token

    def update_token_permissions(
        self, user, token, create=None, read=None, update=None, delete=None
    ):
        """
        Updates create, read, update and delete permissions of the provided token.

        Example:

        TokenHandler().update_token_permissions(
            token=token,
            create=[Database.objects.get(pk=1), Table.objects.get(pk=10)],
            read=True,
            update=False,
            delete=None
        )

        * Gives create row permissions to all tables in database 1 and to table 10.
        * Gives read permissions to all tables in the token's group.
        * Doesn't give permissions to update any row in all the tables related to the
          token's group.
        * Doesn't give permissions to delete any row in all the tables related to the
          token's group.

        :param user: The user on whose behalf the permissions are updated.
        :type user: User
        :param token: The token for which the permissions need to be updated.
        :type token: Token
        :param create: Indicates for which tables the token can create rows. True
            indicates all tables in the group, a database indicates all tables in the
            provided databases and a table indicates only that table. Multiple values
            can be provided in a list.
        :type create: list, bool or none
        :param read: Indicates for which tables the token can list and get rows. True
            indicates all tables in the group, a database indicates all tables in the
            provided databases and a table indicates only that table. Multiple values
            can be provided in a list.
        :type read: list, bool or none
        :param update: Indicates for which tables the token can update rows. True
            indicates all tables in the group, a database indicates all tables in the
            provided databases and a table indicates only that table. Multiple values
            can be provided in a list.
        :type update: list, bool or none
        :param delete: Indicates for which tables the token can delete rows. True
            indicates all tables in the group, a database indicates all tables in the
            provided databases and a table indicates only that table. Multiple values
            can be provided in a list.
        :type delete: list, bool or none
        :raises DatabaseDoesNotBelongToGroup: If a provided database instance does not
            belong to the token's group.
        :raises TableDoesNotBelongToGroup: If a provided table instance does not
            belong to the token's group.
        :raises TokenDoesNotBelongToUser: When the provided token does not belong the
            provided user.
        """

        if not user.id == token.user_id:
            raise TokenDoesNotBelongToUser(
                "The user is not authorized to delete the " "token."
            )

        existing_permissions = token.tokenpermission_set.all()
        desired_permissions = []
        types = ["create", "read", "update", "delete"]

        # Create a list of desired tokens based on the provided create, read, update
        # and delete parameters.
        for type_name in types:
            value = locals()[type_name]

            if value is True:
                desired_permissions.append(TokenPermission(token=token, type=type_name))
            elif isinstance(value, list):
                for instance in value:
                    if isinstance(instance, Database):
                        if instance.group_id != token.group_id:
                            raise DatabaseDoesNotBelongToGroup(
                                f"The database {instance.id} does not belong to the "
                                f"token's group."
                            )

                        desired_permissions.append(
                            TokenPermission(
                                token=token, type=type_name, database_id=instance.id
                            )
                        )
                    elif isinstance(instance, Table):
                        if instance.database.group_id != token.group_id:
                            raise TableDoesNotBelongToGroup(
                                f"The table {instance.id} does not belong to the "
                                f"token's group."
                            )

                        desired_permissions.append(
                            TokenPermission(
                                token=token, type=type_name, table_id=instance.id
                            )
                        )

        def equals(permission_1, permission_2):
            """
            Checks if the two provided permissions are the same.
            """

            return (
                permission_1.token_id == permission_2.token_id
                and permission_1.type == permission_2.type
                and permission_1.database_id == permission_2.database_id
                and permission_1.table_id == permission_2.table_id
            )

        # Check which existing permissions must be deleted by comparing them to the
        # desired permissions.
        to_delete = [
            existing.id
            for existing in existing_permissions
            if not any([equals(existing, desired) for desired in desired_permissions])
        ]

        # Check which permission must be created by comparing them to the existing
        # permissions.
        to_create = [
            desired
            for desired in desired_permissions
            if not any([equals(desired, existing) for existing in existing_permissions])
        ]

        # Delete the permissions that must be delete in bulk.
        if len(to_delete) > 0:
            TokenPermission.objects.filter(id__in=to_delete).delete()

        # Create the permissions that must be created in bulk.
        if len(to_create) > 0:
            TokenPermission.objects.bulk_create(to_create)

    def has_table_permission(self, token, type_name, table):
        """
        Checks if the provided token has access to perform an operation on the provided
        table.

        :param token: The token instance.
        :type token: Token
        :param type_name: The CRUD operation, create, read, update or delete to check
            the permissions for. Can be a list if you want to check at least one of the
            listed operation.
        :type type_name: str | list
        :param table: The table object to check the permissions for.
        :type table: Table
        :return: Indicates if the token has permissions to perform the operation on
            the provided table.
        :rtype: bool
        """

        if token.group_id != table.database.group_id:
            return False

        if not table.database.group.has_user(token.user):
            return False

        if isinstance(type_name, str):
            type_names = [type_name]
        else:
            type_names = type_name

        return TokenPermission.objects.filter(
            Q(database__table=table)
            | Q(table_id=table.id)
            | Q(table__isnull=True, database__isnull=True),
            token=token,
            type__in=type_names,
        ).exists()

    def check_table_permissions(
        self, request_or_token, type_name, table, force_check=False
    ):
        """
        Instead of returning True or False, this method will raise an exception if the
        token does not have permission to the table.

        :param request_or_token: If a request is provided then the token will be
            extracted from the request. Otherwise a token object is expected.
        :type request_or_token: Request or Token
        :param type_name: The CRUD operation, create, read, update or delete to check
            the permissions for. Can be a list if you want to check at least one of the
            listed operation.
        :type type_name: str | list
        :param table: The table object to check the permissions for.
        :type table: Table
        :param force_check: Indicates if a NoPermissionToTable exception must be raised
            when the token could not be extracted from the request. This can be
            useful if a view accepts multiple types of authentication.
        :type force_check: bool
        :raises ValueError: when neither a Token or HttpRequest is provided.
        :raises NoPermissionToTable: when the token does not have permissions to the
            table.
        """

        token = None

        if not isinstance(request_or_token, Request) and not isinstance(
            request_or_token, Token
        ):
            raise ValueError(
                "The provided instance should be a HttpRequest or Token " "object."
            )

        if isinstance(request_or_token, Request) and hasattr(
            request_or_token, "user_token"
        ):
            token = request_or_token.user_token

        if isinstance(request_or_token, Token):
            token = request_or_token

        if not token and not force_check:
            return

        if (
            not token
            and force_check
            or not TokenHandler().has_table_permission(token, type_name, table)
        ):
            raise NoPermissionToTable(
                f"The provided token does not have {type_name} "
                f"permissions to table {table.id}."
            )

    def delete_token(self, user, token):
        """
        Deletes an existing token

        :param user: The user on whose behalf the token is deleted.
        :type user: User
        :param token: The token object that needs to be deleted.
        :type token: Token
        :raises TokenDoesNotBelongToUser: When the provided token does not belong the
            provided user.
        """

        if not user.id == token.user_id:
            raise TokenDoesNotBelongToUser(
                "The user is not authorized to delete the " "token."
            )

        token.delete()

    def update_token_usage(self, token):
        """
        Increases the amount of handled calls and updates the last call timestamp of
        the token.

        :param token: The token instance that needs to be updated.
        :param token: Token
        :return: The updated token instance.
        :rtype: Token
        """

        token.handled_calls += 1
        token.last_call = timezone.now()
        token.save()

        return token
