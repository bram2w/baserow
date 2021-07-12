from baserow.core.mixins import make_trashable_mixin

ParentFieldTrashableModelMixin = make_trashable_mixin("field")
ParentTableTrashableModelMixin = make_trashable_mixin("table")
