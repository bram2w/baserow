"""
Patch para aplicar filtros de filas basados en permisos de usuario
Intercepta AMBOS casos: con view_id y sin view_id
"""

from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.api.rows.views import RowsView  
from baserow.contrib.database.user_permissions.handler import UserPermissionHandler
from baserow.contrib.database.table.handler import TableHandler
from django.db.models import Q, QuerySet
import inspect

# ====== PATCH 1: ViewHandler.apply_filters (para cuando HAY view_id) ======
_original_apply_filters = ViewHandler.apply_filters

def patched_apply_filters(self, view, queryset: QuerySet) -> QuerySet:
    """Aplica filtros de vista + filtros de permisos de usuario"""
    # Llamar al método original
    queryset = _original_apply_filters(self, view, queryset)
    
    # Buscar el request en el stack
    request = None
    for frame_info in inspect.stack():
        frame_locals = frame_info.frame.f_locals
        if 'request' in frame_locals and hasattr(frame_locals['request'], 'user'):
            request = frame_locals['request']
            break
    
    if not request or not request.user.is_authenticated:
        return queryset
    
    try:
        table = view.table
        user = request.user
        
        print(f"🔎 [ROW FILTER VIEW] Usuario: {user.email}, Tabla: {table.name}")
        
        queryset = _apply_user_row_filter(table, user, queryset)
    except Exception as e:
        print(f"⚠️ [ROW FILTER VIEW] Error: {e}")
        import traceback
        traceback.print_exc()
    
    return queryset

ViewHandler.apply_filters = patched_apply_filters

# ====== PATCH 2: Interceptar el queryset en RowsView cuando NO hay view_id ======
_original_rows_get = RowsView.get

def patched_rows_get(self, request, table_id, query_params):
    """Interceptar para almacenar request y table_id en thread-local"""
    import threading
    if not hasattr(threading, '_row_filter_data'):
        threading._row_filter_data = threading.local()
    
    threading._row_filter_data.request = request
    threading._row_filter_data.table_id = table_id
    
    return _original_rows_get(self, request, table_id, query_params)

RowsView.get = patched_rows_get

# ====== PATCH 3: Interceptar table.get_model() para parchear el queryset ======
from baserow.contrib.database.table.models import Table

_original_get_model = Table.get_model

def patched_get_model(self, **kwargs):
    """Interceptar get_model para parchear el manager del modelo"""
    model = _original_get_model(self, **kwargs)
    
    # Patchear el manager objects si no está ya patcheado
    if not hasattr(model.objects, '_user_filter_patched'):
        _original_all = model.objects.all
        
        def patched_all():
            """Interceptar .all() para aplicar filtros de usuario"""
            queryset = _original_all()
            
            # Obtener request desde thread-local
            import threading
            if hasattr(threading, '_row_filter_data'):
                data = threading._row_filter_data
                if hasattr(data, 'request') and hasattr(data, 'table_id'):
                    request = data.request
                    table_id = data.table_id
                    
                    if request.user.is_authenticated and self.id == table_id:
                        print(f"🔎 [ROW FILTER NO-VIEW] Usuario: {request.user.email}, Tabla: {self.name}")
                        
                        try:
                            queryset = _apply_user_row_filter(self, request.user, queryset)
                        except Exception as e:
                            print(f"⚠️ [ROW FILTER NO-VIEW] Error: {e}")
            
            return queryset
        
        model.objects.all = patched_all
        model.objects._user_filter_patched = True
    
    return model

Table.get_model = patched_get_model

# ====== FUNCIÓN COMÚN para aplicar filtros ======
def _apply_user_row_filter(table, user, queryset):
    """Aplica el filtro de permisos de usuario al queryset"""
    permission_handler = UserPermissionHandler()
    user_rule = permission_handler.get_user_permission_rule(table, user)
    
    if user_rule:
        print(f"🔎 [ROW FILTER] Regla encontrada: Active={user_rule.is_active}, Filter={user_rule.row_filter}")
    
    if user_rule and user_rule.is_active and user_rule.row_filter:
        row_filter = user_rule.row_filter
        filters = row_filter.get('filters', [])
        
        if filters:
            print(f"🔍 [ROW FILTER] Aplicando {len(filters)} filtro(s)")
            
            filter_q = Q()
            for filter_def in filters:
                field_id = filter_def.get('field')
                filter_type = filter_def.get('type')
                value = filter_def.get('value')
                
                print(f"🔍 [ROW FILTER] field_{field_id} {filter_type} {value}")
                
                if filter_type == 'equal':
                    filter_q &= Q(**{f'field_{field_id}': value})
                elif filter_type == 'not_equal':
                    filter_q &= ~Q(**{f'field_{field_id}': value})
            
            count_before = queryset.count()
            queryset = queryset.filter(filter_q)
            count_after = queryset.count()
            print(f"✅ [ROW FILTER] Filtrado: {count_before} → {count_after}")
    
    return queryset

print("✅ Row filter patch applied - Multi-point interception (ViewHandler + RowsView + Table.get_model)")
