import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router'
import { useNuxtApp } from '#app'
import { getEnabledModelsForAIProviderFeature } from '@baserow/modules/core/aiProviderModelFeatureTypes'
import { notifyIf } from '@baserow/modules/core/utils/error'
import ApplicationService from '@baserow/modules/core/services/application'
import AgentApplicationService from '@baserow/modules/agent/services/agentApplication'
import { selectAgentApplication } from '@baserow/modules/agent/middleware/selectAgentApplication'

const CONFIGURATION_FIELDS = [
  'instructions',
  'provider_type',
  'model_identifier',
]

const emptyConfiguration = () => ({
  instructions: '',
  provider_type: null,
  model_identifier: null,
})

/** Page-local Agent configuration, kept out of the shared application store. */
export function useAgentConfiguration(agent) {
  const store = useStore()
  const { $client, $hasPermission } = useNuxtApp()
  const service = AgentApplicationService($client)
  const applicationService = ApplicationService($client)
  const permission = (operation) =>
    Boolean(
      agent.value &&
      $hasPermission(operation, agent.value, agent.value.workspace.id)
    )

  const canReadConfiguration = computed(() =>
    permission('agent_application.read_configuration')
  )
  const canUpdateConfiguration = computed(
    () => canReadConfiguration.value && permission('application.update')
  )

  const name = ref(agent.value?.name ?? '')
  const readiness = computed(() => agent.value?.readiness ?? null)
  const readinessError = ref(false)
  // The first load starts on mount, so the server renders the same pending state.
  const availabilityLoading = ref(canReadConfiguration.value)
  const availabilityError = ref(false)
  const configuration = reactive(emptyConfiguration())
  const savedConfiguration = ref(null)
  const configurationErrors = ref({})
  const configurationLoading = ref(canReadConfiguration.value)
  const configurationLoadError = ref(false)
  const pendingConfiguration = reactive({})
  const savingConfiguration = ref(false)
  const configurationSaveError = ref(false)

  let scope = 0
  let readinessRequest = 0
  let availabilityRequest = 0
  let configurationRequest = 0
  let refreshPending = false
  let inFlightConfiguration = {}
  let configurationSavePromise = null

  const workspace = computed(() =>
    agent.value
      ? store.getters['workspace/get'](agent.value.workspace.id)
      : null
  )
  const enabledModels = computed(() =>
    getEnabledModelsForAIProviderFeature(workspace.value, 'ai_agent')
  )
  const hasPendingConfiguration = computed(
    () => Object.keys(pendingConfiguration).length > 0
  )
  const fieldErrors = computed(() => {
    const saved = savedConfiguration.value
    if (!canReadConfiguration.value || !saved) return {}

    const errors = {}
    for (const field of CONFIGURATION_FIELDS) {
      if (!(configuration[field] || '').trim()) {
        errors[field] = 'required'
      } else if (
        configurationErrors.value[field] === 'unavailable' &&
        configuration[field] === saved[field] &&
        (field !== 'model_identifier' ||
          configuration.provider_type === saved.provider_type)
      ) {
        // The backend's error outranks an older cached model list.
        errors[field] = 'unavailable'
      }
    }
    if (!availabilityLoading.value && !availabilityError.value) {
      const provider = configuration.provider_type
      const models = enabledModels.value[provider] || []
      if (provider && !models.length) errors.provider_type = 'unavailable'
      if (
        provider &&
        configuration.model_identifier &&
        !models.includes(configuration.model_identifier)
      ) {
        errors.model_identifier = 'unavailable'
      }
    }
    return errors
  })
  const scopeIsCurrent = (currentScope) => scope === currentScope

  function updateApplication(data) {
    return store.dispatch('application/forceUpdate', {
      application: agent.value,
      data,
    })
  }

  async function renameAgent() {
    const trimmed = name.value.trim()
    if (!trimmed || trimmed === agent.value.name) {
      name.value = agent.value.name
      return
    }
    try {
      await store.dispatch('application/update', {
        application: agent.value,
        values: { name: trimmed },
      })
    } catch (error) {
      name.value = agent.value.name
      notifyIf(error, 'application')
    }
  }

  async function fetchAgentReadiness() {
    if (!agent.value) return
    const currentScope = scope
    const agentId = agent.value.id
    const request = ++readinessRequest
    readinessError.value = false
    try {
      // Use the ordinary application read so agent_loaded stays once per visit.
      const { data } = await applicationService.get(agentId)
      if (scopeIsCurrent(currentScope) && request === readinessRequest) {
        await updateApplication({ name: data.name, readiness: data.readiness })
      }
    } catch {
      if (scopeIsCurrent(currentScope) && request === readinessRequest) {
        readinessError.value = true
      }
    }
  }

  async function fetchAvailability() {
    if (!canReadConfiguration.value) return
    const currentScope = scope
    const workspaceId = agent.value.workspace.id
    const request = ++availabilityRequest
    availabilityLoading.value = true
    availabilityError.value = false
    try {
      await store.dispatch('workspace/refreshGenerativeAIModels', workspaceId)
    } catch {
      if (scopeIsCurrent(currentScope) && request === availabilityRequest) {
        availabilityError.value = true
      }
    } finally {
      if (scopeIsCurrent(currentScope) && request === availabilityRequest) {
        availabilityLoading.value = false
      }
    }
  }

  function applyConfiguration(data) {
    const saved = Object.fromEntries(
      CONFIGURATION_FIELDS.map((field) => [field, data[field]])
    )
    savedConfiguration.value = saved
    for (const field of CONFIGURATION_FIELDS) {
      if (!(field in pendingConfiguration)) configuration[field] = saved[field]
      if (configuration[field] === saved[field]) {
        delete pendingConfiguration[field]
      }
    }
    configurationErrors.value = data.errors || {}
    ++readinessRequest
    readinessError.value = false
    // Keep only public metadata in the shared application store.
    updateApplication({ readiness: data.state })
  }

  async function fetchConfiguration() {
    if (!canReadConfiguration.value) return
    if (hasPendingConfiguration.value || savingConfiguration.value) {
      refreshPending = true
      return
    }
    const currentScope = scope
    const agentId = agent.value.id
    const request = ++configurationRequest
    configurationLoading.value = !savedConfiguration.value
    configurationLoadError.value = false
    try {
      const { data } = await service.getConfiguration(agentId)
      if (
        scopeIsCurrent(currentScope) &&
        request === configurationRequest &&
        canReadConfiguration.value
      ) {
        applyConfiguration(data)
      }
    } catch {
      if (scopeIsCurrent(currentScope) && request === configurationRequest) {
        configurationLoadError.value = true
      }
    } finally {
      if (scopeIsCurrent(currentScope) && request === configurationRequest) {
        configurationLoading.value = false
      }
    }
  }

  function updateConfiguration(values) {
    if (!canUpdateConfiguration.value) return
    for (const [field, value] of Object.entries(values)) {
      if (!CONFIGURATION_FIELDS.includes(field)) continue
      const normalized =
        ['provider_type', 'model_identifier'].includes(field) && !value
          ? null
          : value
      configuration[field] = normalized
      if (
        savedConfiguration.value?.[field] === normalized &&
        !(field in inFlightConfiguration)
      ) {
        delete pendingConfiguration[field]
      } else {
        pendingConfiguration[field] = normalized
      }
    }
    configurationSaveError.value = false
  }

  function saveConfiguration() {
    // A blur during a save commits its edit once that save finishes.
    if (savingConfiguration.value) {
      return configurationSavePromise.then(saveConfiguration)
    }
    if (!canUpdateConfiguration.value || !hasPendingConfiguration.value) {
      return false
    }
    const currentScope = scope
    const agentId = agent.value.id
    const values = { ...pendingConfiguration }
    savingConfiguration.value = true
    inFlightConfiguration = values
    configurationSaveError.value = false
    ++configurationRequest
    configurationSavePromise = (async () => {
      try {
        const { data } = await service.updateConfiguration(agentId, values)
        if (!scopeIsCurrent(currentScope) || !canReadConfiguration.value) {
          return false
        }
        for (const field of Object.keys(values)) {
          if (configuration[field] === values[field]) {
            delete pendingConfiguration[field]
          }
        }
        applyConfiguration(data)
        return true
      } catch {
        if (scopeIsCurrent(currentScope) && canReadConfiguration.value) {
          configurationSaveError.value = true
        }
        return false
      } finally {
        if (scopeIsCurrent(currentScope)) {
          if (!canReadConfiguration.value) fetchAgentReadiness()
          savingConfiguration.value = false
          inFlightConfiguration = {}
          if (
            refreshPending &&
            !hasPendingConfiguration.value &&
            !configurationSaveError.value
          ) {
            refreshPending = false
            refreshConfiguration()
          }
        }
      }
    })()
    return configurationSavePromise
  }

  async function flushConfiguration() {
    const currentScope = scope
    while (scopeIsCurrent(currentScope) && hasPendingConfiguration.value) {
      const saved = await saveConfiguration()
      if (!saved || configurationSaveError.value) break
    }
    return !scopeIsCurrent(currentScope) || !hasPendingConfiguration.value
  }

  onBeforeRouteLeave(flushConfiguration)
  onBeforeRouteUpdate(async (to, from) => {
    if (await flushConfiguration()) return true
    // Page middleware selects the next Agent before update guards run.
    await selectAgentApplication(useNuxtApp(), from)
    return false
  })

  async function refreshConfiguration({ refreshAgent = true } = {}) {
    await Promise.all([
      refreshAgent && fetchAgentReadiness(),
      fetchAvailability(),
      fetchConfiguration(),
    ])
  }

  function clearConfiguration() {
    ++configurationRequest
    Object.assign(configuration, emptyConfiguration())
    savedConfiguration.value = null
    configurationErrors.value = {}
    configurationLoading.value = false
    Object.keys(pendingConfiguration).forEach(
      (field) => delete pendingConfiguration[field]
    )
    configurationSaveError.value = false
  }

  function reset() {
    ++scope
    clearConfiguration()
    readinessError.value = false
    availabilityLoading.value = false
    availabilityError.value = false
    configurationLoadError.value = false
    savingConfiguration.value = false
    inFlightConfiguration = {}
    configurationSavePromise = null
    refreshPending = false
  }

  onMounted(() => refreshConfiguration({ refreshAgent: false }))
  watch(
    () => [agent.value?.id, store.state.auth.user?.id],
    () => {
      reset()
      if (agent.value) refreshConfiguration({ refreshAgent: false })
    }
  )
  watch(
    () => agent.value?.name,
    (value) => (name.value = value ?? '')
  )
  watch(
    () => JSON.stringify(enabledModels.value),
    () => {
      fetchAgentReadiness()
      fetchConfiguration()
    }
  )
  watch(canReadConfiguration, (allowed) => {
    if (allowed) {
      fetchAvailability()
      fetchConfiguration()
    } else {
      ++availabilityRequest
      availabilityLoading.value = false
      availabilityError.value = false
      clearConfiguration()
      fetchAgentReadiness()
    }
  })
  onBeforeUnmount(reset)

  return {
    canReadConfiguration,
    canUpdateConfiguration,
    name,
    readiness,
    readinessError,
    availabilityLoading,
    availabilityError,
    enabledModels,
    configuration,
    fieldErrors,
    configurationLoading,
    configurationLoadError,
    savingConfiguration,
    configurationSaveError,
    renameAgent,
    updateConfiguration,
    saveConfiguration,
    refreshConfiguration,
  }
}
