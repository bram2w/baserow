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
const agentId = Number(useRoute().params.agentId)
const agent = computed(() => {
  const application = $store.getters['application/get'](agentId)
  return application?.type === 'agent' ? application : null
})
useHead(() => ({ title: agent.value?.name }))

await usePageAsyncData(`agent-${agentId}`, async () => {
  try {
    const { data } = await AgentApplicationService($client).get(agentId)
    await $store.dispatch('application/forceUpdate', {
      application: agent.value,
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
