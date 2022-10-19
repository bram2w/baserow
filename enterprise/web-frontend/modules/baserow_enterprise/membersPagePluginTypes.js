import CrudTableColumn from '@baserow/modules/core/crud_table/crudTableColumn'
import DropdownField from '@baserow/modules/core/components/crud_table/fields/DropdownField'
import { roles } from '@baserow_enterprise/enums/roles'
import { MembersPagePluginType } from '@baserow/modules/database/membersPagePluginTypes'

export class EnterpriseMembersPagePluginType extends MembersPagePluginType {
  static getType() {
    return 'enterprise_members_columns'
  }

  mutateMembersTableRightColumns(rightColumns) {
    return this._replaceRoleColumn(rightColumns)
  }

  mutateMembersInvitesTableRightColumns(rightColumns) {
    return this._replaceRoleColumn(rightColumns)
  }

  isDeactivated() {
    return false // TODO make this depending on if somebody has RBAC
  }

  _replaceRoleColumn(columns) {
    const existingRoleColumnIndex = columns.findIndex(
      (column) => column.key === 'permissions'
    )
    columns[existingRoleColumnIndex] = new CrudTableColumn(
      'permissions', // TODO use the key that holds the RBAC role data in the response
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
        // disabled: (row) => row.user_id === this.userId,
        inputCallback: () => console.log('implement me'), // TODO update role
      }
    )
    return columns
  }
}
