"""
Initial migration for User Permissions models
Ubicación: backend/src/baserow/contrib/database/user_permissions/migrations/0001_initial.py
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('database', '0200_fix_to_timestamptz_formula'),  # Depende de la última migración de database
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPermissionRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)), 
                ('trashed', models.BooleanField(default=False)),
                ('order', models.DecimalField(decimal_places=20, default=0, max_digits=40)),
                ('role', models.CharField(
                    choices=[
                        ('admin', 'Admin'),
                        ('manager', 'Manager'), 
                        ('coordinator', 'Coordinator'),
                        ('viewer', 'Viewer')
                    ],
                    default='viewer',
                    max_length=20,
                    help_text='Base role defining default permissions level'
                )),
                ('row_filter', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text="JSON filter to limit visible rows using user context variables. Example: {'assigned_to': '{user.id}', 'department': '{user.department}'}"
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='Whether this permission rule is currently active'
                )),
                ('table', models.ForeignKey(
                    help_text='Table to which this permission rule applies',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='user_permission_rules',
                    to='database.table'
                )),
                ('user', models.ForeignKey(
                    help_text='User to whom this permission rule applies',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='permission_rules',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'db_table': 'database_user_permission_rule',
            },
        ),
        migrations.CreateModel(
            name='UserFilteredView',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('trashed', models.BooleanField(default=False)),
                ('name', models.CharField(
                    max_length=255,
                    help_text='Display name for this filtered view'
                )),
                ('user_filters', models.JSONField(
                    blank=True,
                    default=dict,
                    help_text='Additional filters applied based on user permissions. These are merged with base_view filters and user permission row_filter'
                )),
                ('visible_fields', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='List of field IDs visible to this user'
                )),
                ('is_default', models.BooleanField(
                    default=False,
                    help_text='Whether this is the default view for the user'
                )),
                ('base_view', models.ForeignKey(
                    blank=True,
                    help_text='Base view to inherit configuration from',
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    to='database.view'
                )),
                ('table', models.ForeignKey(
                    help_text='Table for which this filtered view is created',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='user_filtered_views',
                    to='database.table'
                )),
                ('user', models.ForeignKey(
                    help_text='User for whom this filtered view is created',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='filtered_views',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'db_table': 'database_user_filtered_view',
            },
        ),
        migrations.CreateModel(
            name='UserFieldPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('permission', models.CharField(
                    choices=[
                        ('read', 'Read'),
                        ('write', 'Write'),
                        ('hidden', 'Hidden')
                    ],
                    default='read',
                    max_length=10,
                    help_text='Permission level for this field'
                )),
                ('field', models.ForeignKey(
                    help_text='Field to which this permission applies',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='user_permissions',
                    to='database.field'
                )),
                ('user_rule', models.ForeignKey(
                    help_text='User permission rule this field permission belongs to',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='field_permissions',
                    to='user_permissions.userpermissionrule'
                )),
            ],
            options={
                'db_table': 'database_user_field_permission',
            },
        ),
        migrations.CreateModel(
            name='UserPermissionAuditLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('action', models.CharField(
                    choices=[
                        ('granted', 'Granted'),
                        ('modified', 'Modified'),
                        ('revoked', 'Revoked'),
                        ('field_permission_set', 'Field Permission Set'),
                        ('field_permission_removed', 'Field Permission Removed')
                    ],
                    max_length=30
                )),
                ('details', models.JSONField(
                    default=dict,
                    help_text='Additional details about the permission change'
                )),
                ('actor_user', models.ForeignKey(
                    help_text='User who made the permission change',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='permission_changes_made',
                    to=settings.AUTH_USER_MODEL
                )),
                ('table', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='permission_audit_logs',
                    to='database.table'
                )),
                ('target_user', models.ForeignKey(
                    help_text='User whose permissions were modified',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='permission_changes_received',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'db_table': 'database_user_permission_audit_log',
            },
        ),
        
        # Índices y constraints
        migrations.AddIndex(
            model_name='userpermissionrule',
            index=models.Index(fields=['table', 'user'], name='database_user_permission_rule_table_user_idx'),
        ),
        migrations.AddIndex(
            model_name='userpermissionrule', 
            index=models.Index(fields=['table', 'role'], name='database_user_permission_rule_table_role_idx'),
        ),
        migrations.AddIndex(
            model_name='userpermissionrule',
            index=models.Index(fields=['user', 'is_active'], name='database_user_permission_rule_user_active_idx'),
        ),
        migrations.AddConstraint(
            model_name='userpermissionrule',
            constraint=models.UniqueConstraint(fields=['table', 'user'], name='database_user_permission_rule_table_user_unique'),
        ),
        
        migrations.AddIndex(
            model_name='userfilteredview',
            index=models.Index(fields=['table', 'user'], name='database_user_filtered_view_table_user_idx'),
        ),
        migrations.AddIndex(
            model_name='userfilteredview',
            index=models.Index(fields=['user', 'is_default'], name='database_user_filtered_view_user_default_idx'),
        ),
        migrations.AddConstraint(
            model_name='userfilteredview',
            constraint=models.UniqueConstraint(fields=['table', 'user'], name='database_user_filtered_view_table_user_unique'),
        ),
        
        migrations.AddIndex(
            model_name='userfieldpermission',
            index=models.Index(fields=['user_rule', 'permission'], name='database_user_field_permission_rule_perm_idx'),
        ),
        migrations.AddIndex(
            model_name='userfieldpermission',
            index=models.Index(fields=['field', 'permission'], name='database_user_field_permission_field_perm_idx'),
        ),
        migrations.AddConstraint(
            model_name='userfieldpermission',
            constraint=models.UniqueConstraint(fields=['user_rule', 'field'], name='database_user_field_permission_rule_field_unique'),
        ),
        
        migrations.AddIndex(
            model_name='userpermissionauditlog',
            index=models.Index(fields=['table', 'created_at'], name='database_user_permission_audit_log_table_created_idx'),
        ),
        migrations.AddIndex(
            model_name='userpermissionauditlog',
            index=models.Index(fields=['target_user', 'created_at'], name='database_user_permission_audit_log_target_created_idx'),
        ),
        migrations.AddIndex(
            model_name='userpermissionauditlog',
            index=models.Index(fields=['actor_user', 'created_at'], name='database_user_permission_audit_log_actor_created_idx'),
        ),
    ]