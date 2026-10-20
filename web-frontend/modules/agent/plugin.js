import { AgentApplicationType } from '@baserow/modules/agent/applicationTypes'
import { AgentLastViewedItemType } from '@baserow/modules/agent/lastViewedItemTypes'
import { AgentApplicationSearchType } from '@baserow/modules/agent/searchTypes'
import { searchTypeRegistry } from '@baserow/modules/core/search/types/registry'

export default defineNuxtPlugin({
  name: 'agent',
  dependsOn: ['core'],
  setup(nuxtApp) {
    const context = { app: nuxtApp }

    nuxtApp.$registry.register('application', new AgentApplicationType(context))
    nuxtApp.$registry.register(
      'lastViewedItem',
      new AgentLastViewedItemType(context)
    )
    searchTypeRegistry.register(new AgentApplicationSearchType(context))
  },
})
