import { ApplicationLastViewedItemType } from '@baserow/modules/core/lastViewedItemTypes'

export class AgentLastViewedItemType extends ApplicationLastViewedItemType {
  static getType() {
    return 'agent'
  }

  getOrder() {
    return 100
  }

  getApplicationTypeName() {
    return 'agent'
  }

  getName() {
    return this.app.$i18n.t('applicationType.agent')
  }

  getParentPath() {
    // The agent is the application itself, so there is no parent to name.
    return []
  }

  getRoute(entry) {
    return {
      name: 'agent-application',
      params: { agentId: entry.item.id },
    }
  }

  getFilterOptions() {
    // Hidden while the rollout flag disables creating agents.
    return this.getApplicationType().canBeCreated()
      ? super.getFilterOptions()
      : []
  }
}
