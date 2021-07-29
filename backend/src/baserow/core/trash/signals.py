import django.dispatch

permanently_deleted = django.dispatch.Signal()
"""
Sent when any trashable item in Baserow is permanently deleted with kwargs containing:

:param trash_item: The actual instance of the trashable item that was deleted.
:param trash_item_id : The id of the item that was deleted as trash_item.id will now be
    None.
:param parent_id: The parent id of the trashable item if required for that type.
"""
