import { MembersPagePluginType } from '@baserow/modules/database/membersPagePluginTypes'
import MembersRoleField from '@baserow_enterprise/components/MembersRoleField'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'

export class EnterpriseMembersPagePluginType extends MembersPagePluginType {
  static getType() {
    return 'enterprise_members_columns'
  }

  mutateMembersTableColumns(columns, context) {
    return this._replaceRoleColumn(columns, context)
  }

  mutateMembersInvitesTableColumns(columns, context) {
    // TODO enable again once you can change the role of an invited user before they accept
    // return this._replaceRoleColumn(columns, context)
    return columns
  }

  isDeactivated() {
    return !this.app.$featureFlags.includes('roles') // TODO make this depending on if somebody has RBAC
  }

  _replaceRoleColumn(columns, { group }) {
    const existingRoleColumnIndex = columns.findIndex(
      (column) => column.key === 'permissions'
    )
    if (existingRoleColumnIndex !== -1) {
      columns[existingRoleColumnIndex] = new CrudTableColumn(
        'role_uid',
        this.app.i18n.t('membersSettings.membersTable.columns.role'),
        MembersRoleField,
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
