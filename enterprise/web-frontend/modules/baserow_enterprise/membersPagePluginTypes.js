import { MembersPagePluginType } from '@baserow/modules/database/membersPagePluginTypes'
import MembersRoleField from '@baserow_enterprise/components/MembersRoleField'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import InvitesRoleField from '@baserow_enterprise/components/InvitesRoleField'

export class EnterpriseMembersPagePluginType extends MembersPagePluginType {
  static getType() {
    return 'enterprise_members_columns'
  }

  mutateMembersTableColumns(columns, context) {
    return this._replaceRoleColumn(
      columns,
      MembersRoleField,
      'role_uid',
      context
    )
  }

  mutateMembersInvitesTableColumns(columns, context) {
    return this._replaceRoleColumn(
      columns,
      InvitesRoleField,
      'permissions',
      context
    )
  }

  isDeactivated() {
    return !this.app.$featureFlags.includes('roles') // TODO make this depending on if somebody has RBAC
  }

  _replaceRoleColumn(columns, FieldComponent, key, { group }) {
    const existingRoleColumnIndex = columns.findIndex(
      (column) => column.key === 'permissions'
    )
    if (existingRoleColumnIndex !== -1) {
      columns[existingRoleColumnIndex] = new CrudTableColumn(
        key,
        this.app.i18n.t('membersSettings.membersTable.columns.role'),
        FieldComponent,
        true,
        false,
        false,
        {
          groupId: group.id,
        }
      )
    }
    return columns
  }
}
