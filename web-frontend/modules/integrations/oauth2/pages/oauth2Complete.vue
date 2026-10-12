<template>
  <div class="loading-absolute-center"></div>
</template>

<script setup>
/**
 * The provider's callback lands here with the code. Completing it with the
 * user's own session, instead of on the backend callback, makes sure only the
 * person who started the flow can attach an account to the integration. The
 * browser then goes back to where the flow started, which shows the outcome.
 */
import OAuth2Service from '@baserow/modules/integrations/oauth2/services/oauth2'
import { getOAuth2Flow } from '@baserow/modules/integrations/oauth2/utils/flow'

definePageMeta({
  middleware: ['settings', 'authenticated'],
})

const route = useRoute()
const nuxtApp = useNuxtApp()

async function getOutcome() {
  const { code, state, error } = route.query
  if (error || !code) {
    return {
      oauth2_status: 'error',
      oauth2_error: route.query.error_description || error || '',
    }
  }
  try {
    const { data } = await OAuth2Service(nuxtApp.$client).complete(code, state)
    return {
      oauth2_status: 'success',
      oauth2_integration: data.integration_id,
    }
  } catch (err) {
    return {
      oauth2_status: 'error',
      oauth2_error: err.response?.data?.detail || '',
    }
  }
}

onMounted(async () => {
  const flow = getOAuth2Flow()
  if (!flow) {
    await navigateTo({ name: 'dashboard' }, { replace: true })
    return
  }
  const outcome = await getOutcome()
  const url = new URL(flow.returnUrl)
  Object.entries(outcome).forEach(([key, value]) => {
    if (value) {
      url.searchParams.set(key, value)
    }
  })
  window.location.replace(url.toString())
})
</script>
