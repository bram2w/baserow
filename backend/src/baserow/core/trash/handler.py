import logging
from typing import Optional, Dict, Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from baserow.core.exceptions import (
    ApplicationNotInGroup,
    GroupDoesNotExist,
    ApplicationDoesNotExist,
    TrashItemDoesNotExist,
)
from baserow.core.models import TrashEntry, Application, Group
from baserow.core.trash.exceptions import (
    CannotRestoreChildBeforeParent,
    ParentIdMustBeProvidedException,
    ParentIdMustNotBeProvidedException,
)
from baserow.core.trash.registries import TrashableItemType, trash_item_type_registry
from baserow.core.trash.signals import permanently_deleted

logger = logging.getLogger(__name__)
User = get_user_model()


class TrashHandler:
    @staticmethod
    def trash(
        requesting_user: User,
        group: Group,
        application: Optional[Application],
        trash_item,
        parent_id=None,
    ) -> TrashEntry:
        """
        Marks the provided trashable item as trashed meaning it will no longer be
        visible or usable in Baserow. However any user with access to its group can
        restore the item after it is trashed to make it visible and usable again. After
        a configurable timeout period or when the a user explicitly empties the
        trash trashed items will be permanently deleted.

        :param parent_id: The id of the parent object if known
        :param requesting_user: The user who is requesting that this item be trashed.
        :param group: The group the trashed item is in.
        :param application: If the item is in an application the application.
        :param trash_item: The item to be trashed.
        :return: A newly created entry in the TrashEntry table for this item.
        """

        # Check if the parent has a trash entry, if so link this new entry to it
        # via a cascading on delete FK to ensure if the parent entry is deleted then
        # this one is also deleted. We do this as say if a table is perm deleted,
        # we don't then want to
        with transaction.atomic():
            trash_item_type = trash_item_type_registry.get_by_model(trash_item)

            _check_parent_id_valid(parent_id, trash_item_type)

            items_to_trash = trash_item_type.get_items_to_trash(trash_item)
            for item in items_to_trash:
                item.trashed = True
                item.save()

            parent = trash_item_type.get_parent(trash_item, parent_id)
            if parent is not None:
                parent_type = trash_item_type_registry.get_by_model(parent)
                parent_name = parent_type.get_name(parent)
            else:
                parent_name = None

            return TrashEntry.objects.create(
                user_who_trashed=requesting_user,
                group=group,
                application=application,
                trash_item_type=trash_item_type.type,
                trash_item_id=trash_item.id,
                name=trash_item_type.get_name(trash_item),
                parent_name=parent_name,
                parent_trash_item_id=parent_id,
                # If we ever introduce the ability to trash many rows at once this
                # call will generate a model per row currently, instead a model cache
                # should be added so generated models can be shared.
                extra_description=trash_item_type.get_extra_description(
                    trash_item, parent
                ),
            )

    @staticmethod
    def restore_item(user, trash_item_type, trash_item_id, parent_trash_item_id=None):
        """
        Restores an item from the trash re-instating it back in Baserow exactly how it
        was before it was trashed.
        :param user: The user requesting to restore trashed item.
        :param trash_item_type: The trashable item type of the item to restore.
        :param parent_trash_item_id: The parent id of the item to restore.
        :param trash_item_id: The trash item id of the item to restore.
        :raises CannotRestoreChildBeforeParent: Raised if the item being restored has
            any parent, or parent of a parent etc which is trashed as that item should
            be restored first.
        """

        with transaction.atomic():
            trashable_item_type = trash_item_type_registry.get(trash_item_type)
            _check_parent_id_valid(parent_trash_item_id, trashable_item_type)

            trash_entry = _get_trash_entry(
                user, trash_item_type, parent_trash_item_id, trash_item_id
            )

            trash_item = trashable_item_type.lookup_trashed_item(trash_entry, {})

            items_to_restore = trashable_item_type.get_items_to_trash(trash_item)

            if TrashHandler.item_has_a_trashed_parent(
                trash_item,
                parent_id=trash_entry.parent_trash_item_id,
            ):
                raise CannotRestoreChildBeforeParent()

            trash_entry.delete()

            # Restore everything in the database first before we run any restored
            # hooks otherwise signals etc might try to be sent when dependent items are
            # still trashed in the database.
            for item in items_to_restore:
                item.trashed = False
                item.save()

            for item in items_to_restore:
                restore_type = trash_item_type_registry.get_by_model(item)
                restore_type.trashed_item_restored(item, trash_entry)

    @staticmethod
    def get_trash_structure(user: User) -> Dict[str, Any]:
        """
        Returns the structure of the trash available to the user. This consists of the
        groups and their applications the user has access to. Each group and application
        indicates whether it itself has been trashed.

        :param user: The user to return the trash structure for.
        :return: An ordered list of groups and their applications which could possibly
            have trash contents.
        """

        structure = {"groups": []}
        groups = _get_groups_excluding_perm_deleted(user)
        for group in groups:
            applications = _get_applications_excluding_perm_deleted(group)
            structure["groups"].append(
                {
                    "id": group.id,
                    "trashed": group.trashed,
                    "name": group.name,
                    "applications": applications,
                }
            )

        return structure

    @staticmethod
    def mark_old_trash_for_permanent_deletion():
        """
        Updates all trash entries which are older than a django setting for permanent
        deletion. Does not perform the deletion itself.
        """

        now = timezone.now()
        hours = settings.HOURS_UNTIL_TRASH_PERMANENTLY_DELETED
        cutoff = now - timezone.timedelta(hours=hours)
        updated_count = TrashEntry.objects.filter(trashed_at__lte=cutoff).update(
            should_be_permanently_deleted=True
        )
        logger.info(
            f"Successfully marked {updated_count} old trash items for deletion as they "
            f"were older than {hours} hours."
        )

    @staticmethod
    def empty(requesting_user: User, group_id: int, application_id: Optional[int]):
        """
        Marks all items in the selected group (or application in the group if
        application_id is provided) as should be permanently deleted.
        """

        with transaction.atomic():
            trash_contents = TrashHandler.get_trash_contents(
                requesting_user, group_id, application_id
            )
            trash_contents.update(should_be_permanently_deleted=True)

    @staticmethod
    def permanently_delete_marked_trash():
        """
        Looks up every trash item marked for permanent deletion and removes them
        irreversibly from the database along with their corresponding trash entries.
        """

        trash_item_lookup_cache = {}
        deleted_count = 0
        for trash_entry in TrashEntry.objects.filter(
            should_be_permanently_deleted=True
        ):
            with transaction.atomic():
                trash_item_type = trash_item_type_registry.get(
                    trash_entry.trash_item_type
                )

                try:
                    to_delete = trash_item_type.lookup_trashed_item(
                        trash_entry, trash_item_lookup_cache
                    )
                    TrashHandler._permanently_delete_and_signal(
                        trash_item_type,
                        to_delete,
                        trash_entry.parent_trash_item_id,
                        trash_item_lookup_cache,
                    )
                except TrashItemDoesNotExist:
                    # When a parent item is deleted it should also delete all of it's
                    # children. Hence we expect that many of these TrashEntries to no
                    # longer point to an existing item. In such a situation we just want
                    # to delete the entry as the item itself has been correctly deleted.
                    pass
                trash_entry.delete()
                deleted_count += 1
        logger.info(
            f"Successfully deleted {deleted_count} trash entries and their associated "
            "trashed items."
        )

    @staticmethod
    def _permanently_delete_and_signal(
        trash_item_type: Any,
        to_delete: Any,
        parent_id: Optional[int],
        trash_item_lookup_cache: Optional[Dict[str, Any]] = None,
    ):
        """
        Internal method which actually permanently deletes the provided to_delete object
        and also triggers the correct signal so plugins can do appropriate clean-up.

        :param trash_item_type: The trashable item type of the item being deleted.
        :param to_delete: The actual instance of the thing to delete.
        :param parent_id: If required for the trashable item type then the id of the
            parent of to_delete.
        :param trash_item_lookup_cache: An optional dictionary used for caching during
            many different invocations of permanently_delete.
        """

        _check_parent_id_valid(parent_id, trash_item_type)
        trash_item_id = to_delete.id
        trash_item_type.permanently_delete_item(
            to_delete,
            trash_item_lookup_cache,
        )
        permanently_deleted.send(
            sender=trash_item_type.type,
            trash_item_id=trash_item_id,
            trash_item=to_delete,
            parent_id=parent_id,
        )

    @staticmethod
    def permanently_delete(trashable_item, parent_id=None):
        """
        Actually removes the provided trashable item from the database irreversibly.
        :param trashable_item: An instance of a TrashableItemType model_class to delete.
        :param parent_id: If required to look-up the item to delete or related items
            this should be set to the parent id of the item to delete.
        """

        trash_item_type = trash_item_type_registry.get_by_model(trashable_item)
        TrashHandler._permanently_delete_and_signal(
            trash_item_type, trashable_item, parent_id
        )

    @staticmethod
    def get_trash_contents(
        user: User, group_id: int, application_id: Optional[int]
    ) -> QuerySet:
        """
        Looks up the trash contents for a particular group optionally filtered by
        the provided application id.
        :param user: The user who is requesting to see the trash contents.
        :param group_id: The group to lookup trash contents inside of.
        :param application_id: The optional application to filter down the trash
            contents to only this group.
        :raises GroupDoesNotExist: If the group_id is for an non
            existent group.
        :raises ApplicationDoesNotExist: If the application_id is for an non
            existent application.
        :raises ApplicationNotInGroup: If the application_id is for an application
            not in the requested group.
        :raises UserNotInGroup: If the user does not belong to the group.
        :return: a queryset of the trash items in the group optionally filtered by
            the provided application.
        """

        group = _get_group(group_id, user)

        application = _get_application(application_id, group, user)

        trash_contents = TrashEntry.objects.filter(
            group=group, should_be_permanently_deleted=False
        )
        if application:
            trash_contents = trash_contents.filter(application=application)
        return trash_contents.order_by("-trashed_at")

    @staticmethod
    def item_has_a_trashed_parent(item, parent_id=None, check_item_also=False):
        """
        Given an instance of a model which is trashable (item) checks if it has a parent
        which is trashed. Returns True if it's parent, or parent's parent (and so on)
        is trashed, False if no parent is trashed.

        :param check_item_also: If true also checks if the provided item itself is
            trashed and returns True if so.
        :param item: An instance of a trashable model to check.
        :param parent_id: If the trashable type of the provided instance requires an
            id to lookup it's parent it must be provided here.
        :return: If the provided item has a trashed parent or not.
        """

        trash_item_type = trash_item_type_registry.get_by_model(item)

        if check_item_also and item.trashed:
            return True

        while True:
            _check_parent_id_valid(parent_id, trash_item_type)
            parent = trash_item_type.get_parent(item, parent_id)
            if parent is None:
                return False
            elif parent.trashed:
                return True
            else:
                item = parent
                # Right now only row the lowest item in the "trash hierarchy" requires
                # a parent id. Hence we know that as we go up into parents we will
                # no longer need parent id's to do the lookups. However if in the future
                # there is an intermediary trashable item which also requires a
                # parent_id this method will not work and will need to be changed.
                parent_id = None
                trash_item_type = trash_item_type_registry.get_by_model(item)


def _get_group(group_id, user):
    try:
        group = Group.objects_and_trash.get(id=group_id)
    except Group.DoesNotExist:
        raise GroupDoesNotExist
    # Check that the group is not marked for perm deletion, if so we don't want
    # to display it's contents anymore as it should be permanently deleted soon.
    try:
        trash_entry = _get_trash_entry(user, "group", None, group.id)
        if trash_entry.should_be_permanently_deleted:
            raise GroupDoesNotExist
    except TrashItemDoesNotExist:
        pass
    group.has_user(user, raise_error=True, include_trash=True)
    return group


def _get_application(application_id, group, user):
    if application_id is not None:
        try:
            application = Application.objects_and_trash.get(id=application_id)
        except Application.DoesNotExist:
            raise ApplicationDoesNotExist()

        try:
            trash_entry = _get_trash_entry(user, "application", None, application.id)
            if trash_entry.should_be_permanently_deleted:
                raise ApplicationDoesNotExist
        except TrashItemDoesNotExist:
            pass

        if application.group != group:
            raise ApplicationNotInGroup()
    else:
        application = None
    return application


def _check_parent_id_valid(
    parent_trash_item_id: Optional[int], trashable_item_type: TrashableItemType
):
    """
    Raises an exception if the parent id is missing when it is required, or when the
    parent id is included when it is not required.

    Because the parent id is stored in the database and used to lookup trash entries
    uniquely, we want to enforce it is not provided when not needed. For example, if
    the API allowed you to provide a parent id when trashing a table, that id will then
    be stored, and it must then be provided when trying to restore that table otherwise
    the entry will not be found. Hence by being strict we ensure it's not possible to
    accidentally trash an item which is hard to then restore.

    :param parent_trash_item_id: The parent id
    :param trashable_item_type: The type to check to see if it needs a parent id or not.
    :return:
    """

    if trashable_item_type.requires_parent_id and parent_trash_item_id is None:
        raise ParentIdMustBeProvidedException()
    if not trashable_item_type.requires_parent_id and parent_trash_item_id is not None:
        raise ParentIdMustNotBeProvidedException()


def _get_groups_excluding_perm_deleted(user):
    groups = Group.objects_and_trash.filter(groupuser__user=user)
    perm_deleted_groups = TrashEntry.objects.filter(
        trash_item_type="group",
        should_be_permanently_deleted=True,
        trash_item_id__in=groups.values_list("id", flat=True),
    ).values_list("trash_item_id", flat=True)
    groups = groups.exclude(id__in=perm_deleted_groups).order_by("groupuser__order")
    return groups


def _get_applications_excluding_perm_deleted(group):
    perm_deleted_apps = TrashEntry.objects.filter(
        trash_item_type="application",
        should_be_permanently_deleted=True,
        trash_item_id__in=group.application_set_including_trash().values_list(
            "id", flat=True
        ),
    ).values_list("trash_item_id", flat=True)
    applications = (
        group.application_set_including_trash()
        .exclude(id__in=perm_deleted_apps)
        .order_by("order", "id")
    )
    return applications


def _get_trash_entry(
    requesting_user: User,
    trash_item_type: str,
    parent_trash_item_id: Optional[int],
    trash_item_id: int,
) -> TrashEntry:
    """
    Gets the trash entry for a particular resource in baserow which has been
    trashed.
    :param trash_item_id: The id of the item to look for a trash entry for.
    :param parent_trash_item_id: The parent id of the item to look for a trash
        entry for.
    :param trash_item_type: The trashable type of the item.
    :param requesting_user: The user requesting to get the trashed item ,
        they must be in the group of the trashed item otherwise this will raise
        UserNotInGroup if not.
    :returns The trash entry for the specified baserow item.
    :raises UserNotInGroup: If the requesting_user is not in the trashed items
        group.
    """

    try:
        trash_entry = TrashEntry.objects.get(
            parent_trash_item_id=parent_trash_item_id,
            trash_item_id=trash_item_id,
            trash_item_type=trash_item_type,
        )
    except TrashEntry.DoesNotExist:
        raise TrashItemDoesNotExist()
    trash_entry.group.has_user(requesting_user, raise_error=True, include_trash=True)
    return trash_entry
