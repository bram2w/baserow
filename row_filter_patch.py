"""
Row-level permissions patch for Baserow.
Intercepts at the model manager level to avoid decorator conflicts.
"""

import logging
from django.db.models import Q, Manager

logger = logging.getLogger(__name__)


def _get_user_from_request(request):
    """Extract user from request (handles both JWT and Token auth)."""
    try:
        # Check for token authentication
        if hasattr(request, 'auth') and request.auth:
            if hasattr(request.auth, 'user'):
                return request.auth.user
        
        # JWT authentication
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            return request.user
            
        return None
    except Exception as e:
        logger.error(f"🔴 [ROW FILTER] Error extracting user: {e}")
        return None


def _apply_user_row_filter(queryset, user, table_id):
    """Apply row-level filtering based on user permissions."""
    try:
        if not user or not user.is_authenticated:
            return queryset
        
        logger.info(f"🔎 [ROW FILTER] Checking filter for user_id={user.id}, table_id={table_id}")
        
        # Get permission rule
        from baserow.contrib.database_user_permissions.handler import UserPermissionHandler
        rule = UserPermissionHandler().get_user_permission_rule(user.id, table_id)
        
        if not rule or not rule.row_filter:
            logger.info(f"✅ [ROW FILTER] No filter configured")
            return queryset
        
        logger.info(f"🔍 [ROW FILTER] Applying filter: {rule.row_filter}")
        
        # Build Q filter from row_filter JSON
        filters = rule.row_filter.get('filters', [])
        filter_type = rule.row_filter.get('filter_type', 'AND')
        
        if not filters:
            return queryset
        
        # Build Q objects
        q_filters = []
        for filter_config in filters:
            field_id = filter_config.get('field')
            filter_type_str = filter_config.get('type', 'equal')
            value = filter_config.get('value')
            
            field_name = f"field_{field_id}"
            
            if filter_type_str == 'equal':
                q_filters.append(Q(**{field_name: value}))
            elif filter_type_str == 'not_equal':
                q_filters.append(~Q(**{field_name: value}))
            elif filter_type_str == 'contains':
                q_filters.append(Q(**{f"{field_name}__icontains": value}))
        
        if not q_filters:
            return queryset
        
        # Combine with AND or OR
        combined_filter = q_filters[0]
        for q in q_filters[1:]:
            if filter_type == 'OR':
                combined_filter |= q
            else:
                combined_filter &= q
        
        # Apply filter
        original_count = queryset.count()
        filtered_queryset = queryset.filter(combined_filter)
        filtered_count = filtered_queryset.count()
        
        logger.info(f"✅ [ROW FILTER] Filtered: {original_count} -> {filtered_count} rows")
        return filtered_queryset
        
    except Exception as e:
        logger.error(f"🔴 [ROW FILTER] Error: {e}", exc_info=True)
        return queryset


# ============================================================================
# STRATEGY: Patch the MANAGER at model creation time (delayed import)
# ============================================================================

def _patch_table_get_model():
    """Apply the patch. Import is done here to avoid circular dependency."""
    from baserow.contrib.database.table.models import Table
    from django.apps import apps
    
    # Store original get_model
    _original_get_model = Table.get_model

    def _patched_get_model(table_instance, **kwargs):
        """Intercept model creation and wrap multiple manager methods."""
        # Get the original model
        model = _original_get_model(table_instance, **kwargs)
        
        # If already patched, return as-is
        if hasattr(model.objects.__class__, '_baserow_row_filter_patched'):
            return model
        
        _patch_model_manager(model, table_instance)
        return model
    
    def _patch_model_manager(model, table_instance):
        """Patch a single model's manager."""
        logger.info(f"🔧 [ROW FILTER] Patching model for table {table_instance.id}")
        
        # Store the original methods
        original_get_queryset = model.objects.get_queryset
        original_all = model.objects.all
        
        def patched_get_queryset():
            """Intercept queryset creation to apply row filters."""
            logger.info(f"🔎 [ROW FILTER] get_queryset() called for table {table_instance.id}")
            queryset = original_get_queryset()
            
            # Try to find request in call stack
            import inspect
            request = None
            
            for frame_info in inspect.stack():
                frame_locals = frame_info.frame.f_locals
                
                # Look for 'self' that has a 'request' attribute (DRF views)
                if 'self' in frame_locals:
                    potential_view = frame_locals['self']
                    if hasattr(potential_view, 'request'):
                        request = potential_view.request
                        break
                
                # Look for 'request' directly
                if 'request' in frame_locals:
                    potential_request = frame_locals['request']
                    if hasattr(potential_request, 'user'):
                        request = potential_request
                        break
            
            if not request:
                logger.info("🔎 [ROW FILTER] No request found in stack")
                return queryset
            
            user = _get_user_from_request(request)
            if not user:
                logger.info("🔎 [ROW FILTER] No user extracted from request")
                return queryset
            
            # Apply filter
            table_id = table_instance.id
            return _apply_user_row_filter(queryset, user, table_id)
        
        def patched_all():
            """Intercept .all() calls."""
            logger.info(f"🔎 [ROW FILTER] all() called for table {table_instance.id}")
            return patched_get_queryset()
        
        # Monkey-patch both methods
        model.objects.get_queryset = patched_get_queryset
        model.objects.all = patched_all
        model.objects.__class__._baserow_row_filter_patched = True
        
        logger.info(f"✅ [ROW FILTER] Patched manager for table {table_instance.id}")

    # Apply the patch to get_model (for future models)
    Table.get_model = _patched_get_model
    
    # IMPORTANT: Patch all EXISTING table models that are already cached
    try:
        from baserow.contrib.database.table.cache import get_cached_model_field_attrs
        # Try to find all cached models
        for model in apps.get_models():
            # Check if it's a Baserow generated table model
            if hasattr(model, '_generated_table_model') and model._generated_table_model:
                # Find the corresponding table instance
                # The model's table name is like "database_table_XYZ"
                if hasattr(model._meta, 'db_table'):
                    table_name = model._meta.db_table
                    if table_name.startswith('database_table_'):
                        table_id_str = table_name.replace('database_table_', '')
                        try:
                            table_id = int(table_id_str)
                            table_instance = Table.objects.get(id=table_id)
                            _patch_model_manager(model, table_instance)
                            logger.info(f"✅ [ROW FILTER] Patched EXISTING model for table {table_id}")
                        except (ValueError, Table.DoesNotExist):
                            pass
    except Exception as e:
        logger.warning(f"⚠️ [ROW FILTER] Could not patch existing models: {e}")
    
    logger.info("✅ Row filter patch applied - intercepting at Manager.get_queryset()")


# Execute patch when module loads (but imports are delayed)
_patch_table_get_model()
