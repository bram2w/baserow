<template>
  <div v-if="filters.length || canCreate" class="dashboard-filters">
    <DashboardFilterControl
      v-for="filter in filters"
      :key="filter.id"
      :filter="filter"
      :applied-values="applied(filter.id)"
      :option-state="options(filter.id)"
      :edit-mode="editMode"
      :selected="selected?.id === filter.id"
      @apply="apply(filter.id, $event)"
      @select="dispatch('selectFilter', filter.id)"
      @options="
        dispatch('fetchFilterOptions', { filterId: filter.id, ...$event })
      "
    />
    <Button
      v-if="canCreate"
      type="secondary"
      icon="iconoir-plus"
      :loading="creating"
      :disabled="creating"
      class="dashboard-filters__add"
      @click="create"
      >{{ $t('dashboardFilter.add') }}</Button
    >
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useNuxtApp } from '#app'
import { notifyIf } from '@baserow/modules/core/utils/error'
import DashboardFilterControl from '@baserow/modules/dashboard/components/filter/DashboardFilterControl'

const props = defineProps({
  dashboard: { type: Object, required: true },
  storePrefix: { type: String, default: '' },
})
const { $store, $hasPermission, $i18n } = useNuxtApp()
const key = computed(() => `${props.storePrefix}dashboardApplication/`)
const getter = (name) => $store.getters[key.value + name]
const dispatch = (name, values) => $store.dispatch(key.value + name, values)
const filters = computed(() => getter('getFilters'))
const editMode = computed(() => getter('isEditMode'))
const selected = computed(() => getter('getSelectedFilter'))
const applied = (id) => getter('getAppliedFilterValues')(id)
const options = (id) => getter('getFilterOptions')(id)
const canCreate = computed(
  () =>
    editMode.value &&
    $hasPermission(
      'dashboard.create_filter',
      props.dashboard,
      props.dashboard.workspace.id
    )
)
const creating = ref(false)
async function create() {
  creating.value = true
  try {
    await dispatch('createFilter', {
      label: $i18n.t('dashboardFilter.defaultLabel'),
      type: 'text',
    })
  } catch (error) {
    notifyIf(error, 'dashboard')
  } finally {
    creating.value = false
  }
}
function apply(filterId, values) {
  return dispatch('applyFilter', { filterId, values })
}
</script>
