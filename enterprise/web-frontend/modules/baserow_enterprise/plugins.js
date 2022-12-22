import { BaserowPlugin } from '@baserow/modules/core/plugins'
import ChatwootSupportSidebarGroup from '@baserow_enterprise/components/ChatwootSupportSidebarGroup'
import MemberRolesDatabaseContextItem from '@baserow_enterprise/components/member-roles/MemberRolesDatabaseContextItem'
import MemberRolesTableContextItem from '@baserow_enterprise/components/member-roles/MemberRolesTableContextItem'
import EnterpriseFeatures from '@baserow_enterprise/features'

export class EnterprisePlugin extends BaserowPlugin {
  static getType() {
    return 'enterprise'
  }

  getSidebarGroupComponent(group) {
    const supportEnabled = this.app.$hasFeature(
      EnterpriseFeatures.SUPPORT,
      group.id
    )
    return supportEnabled ? ChatwootSupportSidebarGroup : null
  }

  getAdditionalDatabaseContextComponents(group, database) {
    if (
      this.app.$hasFeature(EnterpriseFeatures.RBAC, group.id) &&
      this.app.$hasPermission('application.read_role', database, group.id) &&
      this.app.$featureFlagIsEnabled('RBAC')
    ) {
      return [MemberRolesDatabaseContextItem]
    } else {
      return []
    }
  }

  getAdditionalTableContextComponents(group, table) {
    if (
      this.app.$hasFeature(EnterpriseFeatures.RBAC, group.id) &&
      this.app.$hasPermission('database.table.read_role', table, group.id) &&
      this.app.$featureFlagIsEnabled('RBAC')
    ) {
      return [MemberRolesTableContextItem]
    } else {
      return []
    }
  }
}
