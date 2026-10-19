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
      @apply="apply(filter.id, $event)"
      @select="dispatch('selectFilter', filter.id)"
      @options="
        dispatch('fetchFilterOptions', { filterId: filter.id, ...$event })
      "
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useNuxtApp } from '#app'
import DashboardFilterControl from '@baserow/modules/dashboard/components/filter/DashboardFilterControl'

const props = defineProps({
  dashboard: { type: Object, required: true },
  storePrefix: { type: String, default: '' },
})
const { $store } = useNuxtApp()
const key = computed(() => `${props.storePrefix}dashboardApplication/`)
const getter = (name) => $store.getters[key.value + name]
const dispatch = (name, values) => $store.dispatch(key.value + name, values)
const filters = computed(() => getter('getFilters'))
const editMode = computed(() => getter('isEditMode'))
const selected = computed(() => getter('getSelectedFilter'))
const applied = (id) => getter('getAppliedFilterValues')(id)
const options = (id) => getter('getFilterOptions')(id)
function apply(filterId, values) {
  return dispatch('applyFilter', { filterId, values })
}
</script>
