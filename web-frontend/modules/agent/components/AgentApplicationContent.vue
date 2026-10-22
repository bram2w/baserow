<template>
  <div class="agent-application">
    <header
      class="layout__col-2-1 header header--space-between agent-application__header"
    >
      <div class="agent-application__header-name">{{ agent.name }}</div>
      <ButtonIcon
        v-if="state.canReadConfiguration"
        icon="iconoir-settings"
        :active="configurationOpen"
        :aria-label="$t('agent.configuration')"
        :title="$t('agent.configuration')"
        :aria-expanded="configurationOpen"
        @click="configurationOpen = !configurationOpen"
      />
    </header>
    <div class="layout__col-2-2 agent-application__content">
      <main class="agent-chat">
        <div class="agent-chat__history">
          <div class="agent-chat__intro">
            <div class="agent-chat__avatar">
              <img :src="agentOrb" alt="" />
            </div>
            <i18n-t scope="global" keypath="agent.talkTo" tag="h1">
              <template #name>
                <span class="agent-chat__intro-name">{{ agent.name }}</span>
              </template>
            </i18n-t>
            <p>{{ $t('agent.chatDescription') }}</p>
          </div>
        </div>
        <div class="agent-chat__footer">
          <Alert
            v-if="showConfigurationWarning"
            type="warning"
            class="agent-chat__warning"
          >
            <template #title>{{ $t(warningTitle) }}</template>
            <p>{{ $t(warningMessage) }}</p>
            <template v-if="warningAction" #actions>
              <Button
                v-if="warningAction === 'reload'"
                type="secondary"
                size="small"
                @click="state.refreshConfiguration"
                >{{ $t('action.retry') }}</Button
              >
              <Button
                v-else-if="warningAction === 'save'"
                type="secondary"
                size="small"
                @click="state.saveConfiguration"
                >{{ $t('action.retry') }}</Button
              >
              <template v-else>
                <ButtonText
                  v-for="field in warningFields"
                  :key="field"
                  button-type="button"
                  type="secondary"
                  size="small"
                  class="alert__actions-button-text alert__actions-button-text--normal agent-chat__warning-link"
                  @click="focusConfiguration(field)"
                >
                  {{ $t(fieldLabels[field]) }}
                </ButtonText>
              </template>
            </template>
          </Alert>
        </div>
      </main>
      <AgentConfigurationSidebar
        v-if="state.canReadConfiguration && configurationOpen"
        ref="configurationSidebar"
        v-model:name="state.name"
        :configuration="state.configuration"
        :errors="state.fieldErrors"
        :enabled-models="state.enabledModels"
        :editable="state.canUpdateConfiguration"
        :loading="state.configurationLoading"
        :load-error="state.configurationLoadError && !state.configurationLoaded"
        :availability-loading="state.availabilityLoading"
        :saving="state.savingConfiguration || state.savingName"
        :name-saving="state.savingName"
        :save-error="state.configurationSaveError"
        @close="configurationOpen = false"
        @rename="state.renameAgent"
        @change="state.updateConfiguration"
        @flush="state.saveConfiguration"
        @reload="state.refreshConfiguration"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, toRef } from 'vue'
import agentOrb from '@baserow/modules/agent/assets/images/agent-orb.svg?url'
import AgentConfigurationSidebar from '@baserow/modules/agent/components/AgentConfigurationSidebar'
import { useAgentConfiguration } from '@baserow/modules/agent/composables/useAgentConfiguration'

const props = defineProps({ agent: { type: Object, required: true } })
const state = reactive(useAgentConfiguration(toRef(props, 'agent')))
const configurationOpen = ref(true)
const configurationSidebar = ref(null)
const fieldLabels = {
  instructions: 'agent.instructions',
  provider_type: 'agent.provider',
  model_identifier: 'agent.model',
}
const warningFields = computed(() => Object.keys(state.fieldErrors))
const hasLoadError = computed(
  () =>
    state.readinessError ||
    (state.canReadConfiguration &&
      (state.availabilityError || state.configurationLoadError))
)
const showConfigurationWarning = computed(() =>
  Boolean(
    hasLoadError.value ||
    (state.canReadConfiguration &&
      (state.configurationSaveError ||
        (!state.configurationLoading && warningFields.value.length))) ||
    ['incomplete', 'unavailable'].includes(state.readiness)
  )
)
const warningAction = computed(() => {
  if (hasLoadError.value) return 'reload'
  if (!state.canUpdateConfiguration) return null
  if (warningFields.value.length) return 'fields'
  return state.configurationSaveError ? 'save' : null
})
const warningTitle = computed(() =>
  hasLoadError.value
    ? 'agent.readinessLoadError'
    : state.configurationSaveError
      ? 'agent.configurationSaveError'
      : 'agent.configurationRequired'
)
const warningMessage = computed(() =>
  hasLoadError.value
    ? 'agent.readinessRetry'
    : state.canUpdateConfiguration
      ? state.readiness === 'unavailable' ||
        state.fieldErrors.model_identifier === 'unavailable'
        ? 'agent.modelUnavailable'
        : 'agent.completeConfiguration'
      : 'agent.configurationPermissionRequired'
)
async function focusConfiguration(field) {
  configurationOpen.value = true
  await nextTick()
  await configurationSidebar.value?.focusField(field)
}
</script>
