import { MembersPagePluginType } from '@baserow/modules/database/membersPagePluginTypes'
import MembersRoleField from '@baserow_enterprise/components/MembersRoleField'
import CrudTableColumn from '@baserow/modules/core/crudTable/crudTableColumn'
import InvitesRoleField from '@baserow_enterprise/components/InvitesRoleField'
import EnterpriseFeatures from '@baserow_enterprise/features'

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

  isDeactivated(groupId) {
    return !this.app.$hasFeature(EnterpriseFeatures.RBAC, groupId)
  }

  _replaceRoleColumn(columns, FieldComponent, key, { group }) {
    const existingRoleColumnIndex = columns.findIndex(
      (column) => column.key === 'permissions'
    )
    if (existingRoleColumnIndex !== -1) {
      columns.splice(
        existingRoleColumnIndex,
        1,
        new CrudTableColumn(
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
      )
    }
    return columns
  }
}
