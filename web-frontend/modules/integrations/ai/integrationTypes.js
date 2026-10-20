import { lazyComponent } from '@baserow/modules/core/utils/lazyComponent'
import { IntegrationType } from '@baserow/modules/core/integrationTypes'

const AIForm = lazyComponent(
  () =>
    import('@baserow/modules/integrations/ai/components/integrations/AIForm')
)

export class AIIntegrationType extends IntegrationType {
  static getType() {
    return 'ai'
  }

  get name() {
    return this.app.$i18n.t('integrationType.ai')
  }

  get iconClass() {
    return 'iconoir-spark'
  }

  get iconColor() {
    return 'muted-blue'
  }

  getSummary(integration) {
    const aiSettings = integration.ai_settings || {}
    const overrideCount = Object.keys(aiSettings).length

    if (overrideCount === 0) {
      return this.app.$i18n.t('aiIntegrationType.inheritingWorkspace')
    }

    return this.app.$i18n.t('aiIntegrationType.overridingProviders', {
      count: overrideCount,
    })
  }

  get formComponent() {
    return AIForm
  }

  getDefaultValues() {
    return {
      ai_settings: {},
    }
  }

  getOrder() {
    return 21
  }
}
