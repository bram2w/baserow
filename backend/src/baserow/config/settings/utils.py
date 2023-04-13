import traceback


def setup_dev_e2e(*args, **kwargs):
    # noinspection PyBroadException
    try:
        from django.contrib.auth import get_user_model

        from baserow.core.db import LockedAtomicTransaction

        User = get_user_model()

        from baserow.core.models import Settings

        with LockedAtomicTransaction(Settings):
            setup_dev_e2e_users_and_instance_id(User, args, kwargs)
    except Exception:  # nosec
        traceback.print_exc()
        print("ERROR setting up dev e2e env, see above for stack.")
        pass


def setup_dev_e2e_users_and_instance_id(User, args, kwargs):
    """
    Responsible for changing the `Setting.instance_id` to "1" and creating
    two "staff" base user accounts on post_migrate.
    """

    from baserow.core.models import Settings

    if Settings.objects.get().instance_id != "1":
        from baserow.core.user.handler import UserHandler

        user_handler = UserHandler()
        from baserow.core.user.exceptions import UserAlreadyExist

        for email in ["dev@baserow.io", "e2e@baserow.io"]:
            uname = email.split("@")[0]
            try:
                user = user_handler.create_user(f"staff-{uname}", email, "testpassword")
            except UserAlreadyExist:
                user = User.objects.get(email=email)
            user.is_staff = True
            user.save()

        Settings.objects.update(instance_id="1")
