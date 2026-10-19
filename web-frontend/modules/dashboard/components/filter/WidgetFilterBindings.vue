<template>
  <FormSection
    v-if="filters.length"
    :title="$t('dashboardFilter.widgetFilters')"
    class="dashboard-filter-bindings"
  >
    <FormGroup
      v-for="filter in filters"
      :key="filter.id"
      :label="filter.label"
      small-label
      class="margin-bottom-2"
    >
      <Dropdown
        :model-value="bindingValue(filter)"
        :disabled="loading || failed || saving || !tableId || !canEdit(filter)"
        :error="isBroken(filter)"
        @update:model-value="bind(filter, $event)"
      >
        <DropdownItem
          :value="null"
          :name="$t('dashboardFilter.notConnected')"
        />
        <DropdownItem
          v-if="isBroken(filter)"
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
      <p v-if="!binding(filter)" class="dashboard-filter-bindings__help">
        {{ $t('dashboardFilter.unboundHelp') }}
      </p>
      <p v-else-if="isBroken(filter)" class="dashboard-filter-bindings__error">
        {{ $t('dashboardFilter.invalidFieldHelp') }}
      </p>
    </FormGroup>
  </FormSection>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useNuxtApp } from '#app'
import FieldService from '@baserow/modules/database/services/field'
import { notifyIf } from '@baserow/modules/core/utils/error'

const props = defineProps({
  dashboard: { type: Object, required: true },
  widget: { type: Object, required: true },
  storePrefix: { type: String, default: '' },
})
const { $store, $client, $hasPermission } = useNuxtApp()
const prefix = computed(() => `${props.storePrefix}dashboardApplication/`)
const filters = computed(() => $store.getters[prefix.value + 'getFilters'])
const tableId = computed(
  () =>
    $store.getters[prefix.value + 'getDataSourceById'](
      props.widget.data_source_id
    )?.table_id
)
const fields = ref([])
const loading = ref(false)
const failed = ref(false)
const saving = ref(false)
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
const binding = (filter) =>
  filter.bindings.find((item) => item.widget_id === props.widget.id)
const isBroken = (filter) =>
  !!binding(filter) &&
  !loading.value &&
  !failed.value &&
  !compatibleFields.value.some((field) => field.id === binding(filter).field_id)
const bindingValue = (filter) =>
  isBroken(filter) ? 'unavailable' : (binding(filter)?.field_id ?? null)
const canEdit = (filter) =>
  $hasPermission(
    'dashboard.filter.update',
    filter,
    props.dashboard.workspace.id
  ) &&
  $hasPermission(
    'dashboard.widget.update',
    props.widget,
    props.dashboard.workspace.id
  )

watch(
  tableId,
  async (id, _, onCleanup) => {
    let current = true
    onCleanup(() => {
      current = false
    })
    fields.value = []
    failed.value = false
    loading.value = !!id
    if (!id) return
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

async function bind(filter, fieldId) {
  const bindings = filter.bindings.filter(
    (item) => item.widget_id !== props.widget.id
  )
  if (fieldId !== null)
    bindings.push({ widget_id: props.widget.id, field_id: fieldId })
  saving.value = true
  try {
    await $store.dispatch(prefix.value + 'updateFilter', {
      filterId: filter.id,
      values: { bindings },
    })
  } catch (error) {
    notifyIf(error, 'dashboard')
  } finally {
    saving.value = false
  }
}
</script>
