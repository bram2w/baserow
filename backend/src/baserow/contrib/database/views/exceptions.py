from baserow.core.exceptions import (
    InstanceTypeDoesNotExist, InstanceTypeAlreadyRegistered
)


class ViewTypeAlreadyRegistered(InstanceTypeAlreadyRegistered):
    pass


class ViewTypeDoesNotExist(InstanceTypeDoesNotExist):
    pass
