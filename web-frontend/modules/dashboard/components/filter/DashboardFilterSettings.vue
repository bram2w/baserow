<template>
  <div class="dashboard-filter-settings">
    <FormGroup
      :label="$t('dashboardFilter.label')"
      required
      small-label
      class="margin-bottom-2"
    >
      <FormInput
        v-model="label"
        :maxlength="255"
        :error="!label?.trim()"
        :disabled="!canEdit"
        @blur="saveLabel"
        @keydown.enter.prevent="saveLabel"
      />
    </FormGroup>
    <FormGroup
      :label="$t('dashboardFilter.type')"
      small-label
      required
      class="margin-bottom-2"
    >
      <Dropdown model-value="text" disabled
        ><DropdownItem
          value="text"
          :name="$t('dashboardFilter.text')"
          icon="iconoir-text"
      /></Dropdown>
    </FormGroup>
    <FormGroup
      :label="$t('dashboardFilter.operator')"
      small-label
      required
      class="margin-bottom-2"
    >
      <Dropdown
        :model-value="filter.operator"
        :disabled="!canEdit"
        @update:model-value="save({ operator: $event })"
      >
        <DropdownItem
          v-for="operator in operators"
          :key="operator"
          :value="operator"
          :name="$t(`dashboardFilter.${operator}`)"
        />
      </Dropdown>
    </FormGroup>
    <FormSection
      :title="$t('dashboardFilter.tableFields')"
      class="dashboard-filter-bindings"
    >
      <p class="dashboard-filter-settings__help">
        {{ $t('dashboardFilter.bindingHelp') }}
      </p>
      <DashboardFilterTableField
        v-for="table in tables"
        :key="table.id"
        :table="table"
        :binding="
          filter.bindings.find((binding) => binding.table_id === table.id)
        "
        :disabled="!canEdit || savingBinding"
        @select="bindTable(table.id, $event)"
      />
      <p v-if="!tables.length" class="dashboard-filter-bindings__help">
        {{ $t('dashboardFilter.noTables') }}
      </p>
    </FormSection>
    <FormGroup
      :label="$t('dashboardFilter.mode')"
      small-label
      required
      class="margin-bottom-2"
    >
      <SegmentControl
        :segments="[
          { label: $t('dashboardFilter.dropdown') },
          { label: $t('dashboardFilter.input') },
        ]"
        :active-index="filter.mode === 'dropdown' ? 0 : 1"
        @update:active-index="
          requestFormatChange({ mode: $event === 0 ? 'dropdown' : 'input' })
        "
      />
    </FormGroup>
    <FormGroup
      v-if="filter.mode === 'dropdown'"
      :label="$t('dashboardFilter.usersCanPick')"
      small-label
      required
      class="margin-bottom-2"
    >
      <SegmentControl
        :segments="[
          { label: $t('dashboardFilter.multiple') },
          { label: $t('dashboardFilter.single') },
        ]"
        :active-index="filter.multiple ? 0 : 1"
        @update:active-index="requestFormatChange({ multiple: $event === 0 })"
      />
    </FormGroup>
    <Modal
      ref="confirmation"
      small
      :can-close="!savingFormat"
      role="dialog"
      aria-modal="true"
      :aria-label="$t('dashboardFilter.confirmResetTitle')"
      @hidden="pendingFormat = null"
    >
      <h2 class="box__head-title margin-bottom-4">
        {{ $t('dashboardFilter.confirmResetTitle') }}
      </h2>
      <p>
        {{
          $t('dashboardFilter.confirmResetMessage', {
            format: pendingFormatLabel,
            filter: filter.label,
          })
        }}
      </p>
      <div class="actions actions--right actions--gap margin-bottom-0">
        <Button
          type="secondary"
          :disabled="savingFormat"
          @click="confirmation.hide()"
        >
          {{ $t('action.cancel') }}
        </Button>
        <Button
          type="primary"
          :loading="savingFormat"
          :disabled="savingFormat || !canEdit || !pendingFormat"
          @click="confirmFormatChange"
        >
          {{ $t('dashboardFilter.confirmReset') }}
        </Button>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useNuxtApp } from '#app'
import DashboardFilterTableField from '@baserow/modules/dashboard/components/filter/DashboardFilterTableField'
import { shouldResetFilterValues } from '@baserow/modules/dashboard/utils/filter'
import { notifyIf } from '@baserow/modules/core/utils/error'

const props = defineProps({
  filter: { type: Object, required: true },
  dashboard: { type: Object, required: true },
  storePrefix: { type: String, default: '' },
})
const { $store, $hasPermission, $i18n } = useNuxtApp()
const label = ref(props.filter.label)
const savingBinding = ref(false)
const confirmation = ref(null)
const pendingFormat = ref(null)
const savingFormat = ref(false)
const pendingFormatLabel = computed(() => {
  if (!pendingFormat.value) return ''
  const { mode, multiple } = pendingFormat.value
  return $i18n.t(
    `dashboardFilter.${mode ?? (multiple ? 'multiple' : 'single')}`
  )
})
const prefix = computed(() => `${props.storePrefix}dashboardApplication/`)
const tables = computed(() => {
  const tableIds = new Set(
    props.filter.bindings.map((binding) => binding.table_id)
  )
  for (const widget of $store.getters[prefix.value + 'getWidgets']) {
    const source = $store.getters[prefix.value + 'getDataSourceById'](
      widget.data_source_id
    )
    if (source?.table_id) tableIds.add(source.table_id)
  }
  const databases = $store.getters[prefix.value + 'getIntegrations'].flatMap(
    (integration) => integration.context_data?.databases || []
  )
  return [...tableIds]
    .toSorted((first, second) => first - second)
    .map((id) => {
      const database = databases.find((database) =>
        database.tables.some((table) => table.id === id)
      )
      const table = database?.tables.find((table) => table.id === id)
      return {
        id,
        name: table
          ? `${database.name} / ${table.name}`
          : $i18n.t('dashboardFilter.tableFallback', { id }),
      }
    })
})
async function bindTable(tableId, fieldId) {
  if (!canEdit.value || savingBinding.value) return
  savingBinding.value = true
  try {
    await save({
      bindings: [
        ...props.filter.bindings.filter(
          (binding) => binding.table_id !== tableId
        ),
        { table_id: tableId, field_id: fieldId },
      ],
    })
  } finally {
    savingBinding.value = false
  }
}
const operators = ['equal', 'not_equal', 'contains', 'contains_not']
const canEdit = computed(() =>
  $hasPermission(
    'dashboard.filter.update',
    props.filter,
    props.dashboard.workspace.id
  )
)
watch(
  () => [props.filter.id, props.filter.label],
  () => {
    label.value = props.filter.label
  }
)
watch(
  [
    () => props.dashboard.id,
    () => props.filter.id,
    () => props.filter.mode,
    () => props.filter.multiple,
  ],
  () => confirmation.value?.hide()
)
onBeforeUnmount(() => confirmation.value?.hide())
function requestFormatChange(values) {
  if (
    !canEdit.value ||
    savingFormat.value ||
    pendingFormat.value ||
    !shouldResetFilterValues(props.filter, { ...props.filter, ...values })
  )
    return
  pendingFormat.value = values
  confirmation.value.show()
}
async function confirmFormatChange() {
  if (!canEdit.value || savingFormat.value || !pendingFormat.value) return
  savingFormat.value = true
  try {
    const updated = await save(pendingFormat.value)
    if (updated) confirmation.value?.hide()
  } finally {
    savingFormat.value = false
  }
}
async function save(values) {
  if (!canEdit.value) return
  try {
    return await $store.dispatch(
      `${props.storePrefix}dashboardApplication/updateFilter`,
      { filterId: props.filter.id, values }
    )
  } catch (error) {
    label.value = props.filter.label
    notifyIf(error, 'dashboard')
  }
}
function saveLabel() {
  if (label.value?.trim() && label.value !== props.filter.label)
    return save({ label: label.value })
}
</script>
