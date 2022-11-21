import { BaserowPlugin } from '@baserow/modules/core/plugins'
import ChatwootSupportSidebarGroup from '@baserow_enterprise/components/ChatwootSupportSidebarGroup'
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
}
