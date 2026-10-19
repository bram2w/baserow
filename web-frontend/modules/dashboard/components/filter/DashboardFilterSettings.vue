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
    <div class="dashboard-filter-settings__separator"></div>
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
          save({ mode: $event === 0 ? 'dropdown' : 'input' })
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
        @update:active-index="save({ multiple: $event === 0 })"
      />
    </FormGroup>
    <p class="dashboard-filter-settings__help">
      {{ $t('dashboardFilter.bindingHelp') }}
    </p>
    <Button
      v-if="canDelete"
      type="secondary"
      :loading="deleting"
      :disabled="deleting"
      icon="iconoir-bin"
      @click="remove"
      >{{ $t('dashboardFilter.delete') }}</Button
    >
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useNuxtApp } from '#app'
import { notifyIf } from '@baserow/modules/core/utils/error'

const props = defineProps({
  filter: { type: Object, required: true },
  dashboard: { type: Object, required: true },
  storePrefix: { type: String, default: '' },
})
const { $store, $hasPermission } = useNuxtApp()
const label = ref(props.filter.label)
const deleting = ref(false)
const operators = ['equal', 'not_equal', 'contains', 'contains_not']
const canEdit = computed(() =>
  $hasPermission(
    'dashboard.filter.update',
    props.filter,
    props.dashboard.workspace.id
  )
)
const canDelete = computed(() =>
  $hasPermission(
    'dashboard.filter.delete',
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
async function save(values) {
  if (!canEdit.value) return
  try {
    await $store.dispatch(
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
async function remove() {
  deleting.value = true
  try {
    await $store.dispatch(
      `${props.storePrefix}dashboardApplication/deleteFilter`,
      props.filter.id
    )
  } catch (error) {
    notifyIf(error, 'dashboard')
  } finally {
    deleting.value = false
  }
}
</script>
