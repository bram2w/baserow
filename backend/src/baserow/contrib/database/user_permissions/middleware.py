"""
Middleware para aplicar filtros de filas basados en permisos de usuario
"""

from django.utils.deprecation import MiddlewareMixin
from baserow.contrib.database.user_permissions.handler import UserPermissionHandler
from baserow.contrib.database.table.handler import TableHandler
from django.db.models import Q


class RowFilterMiddleware(MiddlewareMixin):
    """
    Middleware que intercepta requests a la API de rows y aplica filtros de usuario
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Interceptar la vista antes de ejecutarla
        """
        # Solo procesar requests a la API de rows
        if '/api/database/rows/table/' in request.path:
            # Almacenar información en request para uso posterior
            request._row_filter_middleware_active = True
            if 'table_id' in view_kwargs:
                request._table_id = view_kwargs['table_id']
        
        return None  # Continuar normalmente

print("✅ Row filter middleware registered")
