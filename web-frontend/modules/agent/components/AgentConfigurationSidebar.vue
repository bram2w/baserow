<template>
  <aside class="agent-configuration" :aria-busy="loading">
    <div class="agent-configuration__header">
      <button
        v-if="selectedSection"
        type="button"
        class="agent-configuration__icon-button"
        :aria-label="$t('action.back')"
        @click="section = null"
      >
        <i class="iconoir-nav-arrow-left" />
      </button>
      <h2>{{ selectedSection?.name || $t('agent.configuration') }}</h2>
      <span class="agent-configuration__save-indicator">
        <span
          v-if="saving"
          class="agent-configuration__saving"
          role="status"
          :aria-label="$t('agent.saving')"
        />
      </span>
      <button
        type="button"
        class="agent-configuration__icon-button"
        :aria-label="$t('action.close')"
        @click="$emit('close')"
      >
        <i class="iconoir-cancel" />
      </button>
    </div>
    <div
      v-if="loading"
      class="agent-configuration__sections skeleton"
      aria-hidden="true"
    >
      <div
        v-for="registeredSection in registeredSections"
        :key="registeredSection.type"
        class="agent-configuration__skeleton-row"
      >
        <SkeletonBlock width="16px" height="16px" />
        <div class="agent-configuration__section-content">
          <SkeletonBlock width="120px" />
          <SkeletonBlock class="margin-top-1" width="180px" height="10px" />
        </div>
      </div>
    </div>
    <div v-else-if="loadError" class="agent-configuration__body">
      <Alert type="error">
        {{ $t('agent.configurationLoadError') }}
        <template #actions
          ><Button type="secondary" size="small" @click="$emit('reload')">{{
            $t('action.retry')
          }}</Button></template
        >
      </Alert>
    </div>
    <template v-else>
      <div v-if="!selectedSection" class="agent-configuration__sections">
        <button
          v-for="registeredSection in registeredSections"
          :key="registeredSection.type"
          type="button"
          class="agent-configuration__section"
          @click="section = registeredSection.type"
        >
          <i
            class="agent-configuration__section-icon"
            :class="registeredSection.icon"
          />
          <span class="agent-configuration__section-content"
            ><strong class="agent-configuration__section-title">{{
              registeredSection.name
            }}</strong
            ><span
              class="agent-configuration__section-description"
              :title="registeredSection.description"
              >{{ registeredSection.description }}</span
            ></span
          >
          <i
            v-if="sectionErrors[registeredSection.type]"
            v-tooltip="sectionErrors[registeredSection.type]"
            tooltip-position="bottom-left"
            class="agent-configuration__section-caret agent-configuration__section-caret--error iconoir-warning-circle"
            role="img"
            :aria-label="sectionErrors[registeredSection.type]"
          />
          <i
            v-else
            class="agent-configuration__section-caret iconoir-nav-arrow-right"
          />
        </button>
      </div>
      <ReadOnlyForm
        v-else
        :read-only="!editable"
        class="agent-configuration__form"
      >
        <form class="agent-configuration__body" @submit.prevent>
          <component
            :is="selectedSection.component"
            ref="sectionComponent"
            :section-type="selectedSection"
            :name="name"
            :configuration="configuration"
            :errors="errors"
            :enabled-models="enabledModels"
            :editable="editable"
            :availability-loading="availabilityLoading"
            :name-saving="nameSaving"
            @update:name="$emit('update:name', $event)"
            @rename="$emit('rename')"
            @change="$emit('change', $event)"
            @flush="$emit('flush')"
          />
        </form>
      </ReadOnlyForm>
      <div
        v-if="saveError"
        class="agent-configuration__save-status"
        aria-live="polite"
      >
        <span>{{ $t('agent.configurationSaveError') }}</span>
        <Button type="secondary" size="small" @click="$emit('flush')">{{
          $t('action.retry')
        }}</Button>
      </div>
    </template>
  </aside>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import ReadOnlyForm from '@baserow/modules/core/components/ReadOnlyForm'

const props = defineProps({
  name: { type: String, required: true },
  configuration: { type: Object, required: true },
  errors: { type: Object, required: true },
  enabledModels: { type: Object, required: true },
  editable: Boolean,
  loading: Boolean,
  loadError: Boolean,
  availabilityLoading: Boolean,
  saving: Boolean,
  nameSaving: Boolean,
  saveError: Boolean,
})
defineEmits(['close', 'update:name', 'rename', 'change', 'flush', 'reload'])
const { $registry } = useNuxtApp()
const section = ref(null)
const sectionComponent = ref(null)
const registeredSections = computed(() =>
  $registry.getOrderedList('agentConfigurationSection')
)
const selectedSection = computed(() =>
  registeredSections.value.find(
    (registered) => registered.type === section.value
  )
)
const sectionErrors = computed(() =>
  Object.fromEntries(
    registeredSections.value.map((registered) => [
      registered.type,
      registered.getErrorMessage(props.errors),
    ])
  )
)

async function focusField(field) {
  const matchingSection = registeredSections.value.find((registered) =>
    Object.hasOwn(registered.fields, field)
  )
  if (!matchingSection) return
  section.value = matchingSection.type
  await nextTick()
  sectionComponent.value?.focusField?.(field)
}

defineExpose({ focusField })
</script>
