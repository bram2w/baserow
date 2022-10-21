import CrudTableColumn from '@baserow/modules/core/crud_table/crudTableColumn'
import DropdownField from '@baserow/modules/core/components/crud_table/fields/DropdownField'
import { roles } from '@baserow_enterprise/enums/roles'
import { MembersPagePluginType } from '@baserow/modules/database/membersPagePluginTypes'
import RoleAssignmentsService from '@baserow_enterprise/services/roleAssignments'

export class EnterpriseMembersPagePluginType extends MembersPagePluginType {
  static getType() {
    return 'enterprise_members_columns'
  }

  mutateMembersTableRightColumns(rightColumns, context) {
    return this._replaceRoleColumn(rightColumns, context)
  }

  mutateMembersInvitesTableRightColumns(rightColumns, context) {
    return this._replaceRoleColumn(rightColumns, context)
  }

  isDeactivated() {
    return !this.app.$featureFlags.includes('roles') // TODO make this depending on if somebody has RBAC
  }

  _replaceRoleColumn(columns, { groupId, client }) {
    const existingRoleColumnIndex = columns.findIndex(
      (column) => column.key === 'permissions'
    )
    if (existingRoleColumnIndex !== -1) {
      columns[existingRoleColumnIndex] = new CrudTableColumn(
        'role_uid',
        this.app.i18n.t('membersSettings.membersTable.columns.role'),
        DropdownField,
        'min-content',
        '3fr',
        true,
        {
          options: roles.map(({ name, uid }) => ({
            value: uid,
            name,
          })),
          inputCallback: (roleUid, row) =>
            RoleAssignmentsService(client).assignRole(
              row.user_id,
              'user',
              groupId,
              groupId,
              'group',
              roleUid
            ),
        }
      )
    }
    return columns
  }
}
