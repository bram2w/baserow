from .registries import ViewType
from .models import GridView


class GridViewType(ViewType):
    type = 'grid'
    model_class = GridView
