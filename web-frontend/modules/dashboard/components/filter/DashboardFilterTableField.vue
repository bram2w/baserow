<template>
  <FormGroup
    :label="table.name"
    small-label
    required
    class="dashboard-filter-table-field margin-bottom-2"
    :error="broken || failed"
    :error-message="
      failed
        ? $t('dashboardFilter.fieldsError')
        : broken
          ? $t('dashboardFilter.invalidFieldHelp')
          : ''
    "
    :helper-text="
      !loading && !failed && !fieldId && !broken
        ? $t('dashboardFilter.missingFieldHelp')
        : ''
    "
  >
    <Dropdown
      :model-value="broken ? 'unavailable' : (fieldId ?? null)"
      :disabled="disabled || loading || failed"
      :error="broken || (!loading && !failed && !fieldId)"
      @update:model-value="$emit('select', $event)"
    >
      <DropdownItem
        :value="null"
        :name="$t('dashboardFilter.chooseField')"
        disabled
      />
      <DropdownItem
        v-if="broken"
        value="unavailable"
        :name="$t('dashboardFilter.invalidField')"
        disabled
      />
      <DropdownItem
        v-for="field in compatibleFields"
        :key="field.id"
        :value="field.id"
        :name="field.name"
        :icon="$registry.get('field', field.type).getIconClass()"
      />
    </Dropdown>
  </FormGroup>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useNuxtApp } from '#app'
import FieldService from '@baserow/modules/database/services/field'
import { notifyIf } from '@baserow/modules/core/utils/error'

const props = defineProps({
  table: { type: Object, required: true },
  binding: { type: Object, default: null },
  disabled: { type: Boolean, default: false },
})
defineEmits(['select'])
const { $client } = useNuxtApp()
const fields = ref([])
const loading = ref(false)
const failed = ref(false)
const textTypes = [
  'text',
  'long_text',
  'email',
  'url',
  'phone_number',
  'single_select',
]
const compatibleFields = computed(() =>
  fields.value.filter(
    (field) =>
      textTypes.includes(field.type) ||
      (field.type === 'formula' &&
        ['text', 'char', 'single_select'].includes(field.formula_type))
  )
)
const fieldId = computed(() => props.binding?.field_id ?? null)
const broken = computed(
  () =>
    !!props.binding &&
    !loading.value &&
    !failed.value &&
    !compatibleFields.value.some((field) => field.id === fieldId.value)
)
watch(
  () => props.table.id,
  async (id, _, onCleanup) => {
    let current = true
    onCleanup(() => {
      current = false
    })
    fields.value = []
    failed.value = false
    loading.value = true
    try {
      const { data } = await FieldService($client).fetchAll(id)
      if (current) fields.value = data
    } catch (error) {
      if (current) {
        failed.value = true
        notifyIf(error, 'dashboard')
      }
    } finally {
      if (current) loading.value = false
    }
  },
  { immediate: true }
)
</script>
