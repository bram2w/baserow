<template>
  <div v-if="filters.length" class="dashboard-filters">
    <DashboardFilterControl
      v-for="filter in filters"
      :key="filter.id"
      :filter="filter"
      :applied-values="applied(filter.id)"
      :option-state="options(filter.id)"
      :edit-mode="editMode"
      :selected="selected?.id === filter.id"
      :can-delete="canDelete(filter)"
      :deleting="deleting"
      @apply="apply(filter.id, $event)"
      @select="dispatch('selectFilter', filter.id)"
      @delete="remove(filter)"
      @reset="notifyReset(filter)"
      @options="
        dispatch('fetchFilterOptions', { filterId: filter.id, ...$event })
      "
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useNuxtApp } from '#app'
import DashboardFilterControl from '@baserow/modules/dashboard/components/filter/DashboardFilterControl'
import { notifyIf } from '@baserow/modules/core/utils/error'

const props = defineProps({
  dashboard: { type: Object, required: true },
  storePrefix: { type: String, default: '' },
})
const { $store, $hasPermission, $i18n } = useNuxtApp()
const deleting = ref(false)
const key = computed(() => `${props.storePrefix}dashboardApplication/`)
const getter = (name) => $store.getters[key.value + name]
const dispatch = (name, values) => $store.dispatch(key.value + name, values)
const filters = computed(() => getter('getFilters'))
const editMode = computed(() => getter('isEditMode'))
const selected = computed(() => getter('getSelectedFilter'))
const applied = (id) => getter('getAppliedFilterValues')(id)
const options = (id) => getter('getFilterOptions')(id)
const canDelete = (filter) =>
  $hasPermission(
    'dashboard.filter.delete',
    filter,
    props.dashboard.workspace.id
  )
function apply(filterId, values) {
  return dispatch('applyFilter', { filterId, values })
}
function notifyReset(filter) {
  return $store.dispatch('toast/info', {
    title: $i18n.t('dashboardFilter.resetTitle'),
    message: $i18n.t(
      filter.mode === 'input'
        ? 'dashboardFilter.resetToInput'
        : 'dashboardFilter.resetToSingle',
      { filter: filter.label }
    ),
  })
}
async function remove(filter) {
  if (!editMode.value || !canDelete(filter) || deleting.value) return
  deleting.value = true
  try {
    await dispatch('deleteFilter', filter.id)
  } catch (error) {
    notifyIf(error, 'dashboard')
  } finally {
    deleting.value = false
  }
}
</script>
