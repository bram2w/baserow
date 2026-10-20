<template>
  <AgentApplicationContent v-if="agent" :agent="agent" />
</template>

<script setup>
import { computed } from 'vue'
import { createError } from '#app'
import AgentApplicationContent from '@baserow/modules/agent/components/AgentApplicationContent'
import AgentApplicationService from '@baserow/modules/agent/services/agentApplication'
import { usePageAsyncData } from '@baserow/modules/core/composables/usePageAsyncData'
import { normalizeError } from '@baserow/modules/database/utils/errors'

definePageMeta({
  layout: 'app',
  middleware: [
    'settings',
    'authenticated',
    'workspacesAndApplications',
    'selectAgentApplication',
  ],
})

const { $store, $client } = useNuxtApp()
const route = useRoute()
const agent = computed(() => {
  const selected = $store.getters['application/get'](
    Number(route.params.agentId)
  )
  return selected?.type === 'agent' ? selected : null
})
useHead(() => ({ title: agent.value?.name }))

// Read once: the next route selects its application before this page unmounts.
const application = agent.value
const agentId = application.id
await usePageAsyncData(`agent-${agentId}`, async () => {
  try {
    const { data } = await AgentApplicationService($client).get(agentId)
    await $store.dispatch('application/forceUpdate', {
      application,
      data: { name: data.name, readiness: data.readiness },
    })
    return true
  } catch (error) {
    if (!error.response) {
      throw error
    }
    const statusCode = error.response.status
    throw createError({
      statusCode,
      message:
        statusCode === 404 ? 'Agent not found.' : normalizeError(error).message,
      data: { report: statusCode >= 500 },
      fatal: true,
    })
  }
})
</script>
