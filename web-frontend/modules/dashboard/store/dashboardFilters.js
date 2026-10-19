import FilterService from '@baserow/modules/dashboard/services/filter'

export const filterState = () => ({
  filters: [],
  selectedFilterId: null,
  appliedFilters: {},
  filterFetchGeneration: 0,
  filterMutationGenerations: {},
  filterOptionGenerations: {},
  filterOptions: {},
  refreshing: false,
})

const dashboardRequest = (state) => ({
  id: state.dashboardId,
  generation: state.dashboardGeneration,
})
const isCurrent = (state, request) =>
  state.dashboardId === request.id &&
  state.dashboardGeneration === request.generation
const emptyOptions = () => ({
  results: [],
  next: null,
  unavailable: [],
  loading: false,
  error: false,
  search: '',
})

export const filterMutations = {
  INVALIDATE_FILTER_FETCH(state) {
    state.filterFetchGeneration += 1
  },
  INVALIDATE_FILTER_MUTATION(state, filterId) {
    state.filterMutationGenerations[filterId] =
      (state.filterMutationGenerations[filterId] ?? 0) + 1
  },
  INVALIDATE_FILTER_OPTIONS(state, filterId) {
    state.filterOptionGenerations[filterId] =
      (state.filterOptionGenerations[filterId] ?? 0) + 1
    if (state.filterOptions[filterId])
      state.filterOptions[filterId].loading = false
  },
  SET_FILTERS(state, filters) {
    state.filters = filters
    const ids = new Set(filters.map((f) => f.id))
    for (const id of Object.keys(state.appliedFilters)) {
      if (!ids.has(Number(id))) delete state.appliedFilters[id]
    }
    if (!ids.has(state.selectedFilterId)) state.selectedFilterId = null
  },
  UPSERT_FILTER(state, filter) {
    const index = state.filters.findIndex((f) => f.id === filter.id)
    if (index === -1) state.filters.push(filter)
    else state.filters.splice(index, 1, filter)
    state.filters.sort((a, b) => a.id - b.id)
  },
  DELETE_FILTER(state, filterId) {
    state.filters = state.filters.filter((f) => f.id !== filterId)
    delete state.appliedFilters[filterId]
    delete state.filterOptions[filterId]
    if (state.selectedFilterId === filterId) state.selectedFilterId = null
  },
  SELECT_FILTER(state, filterId) {
    state.selectedFilterId = filterId
    state.selectedWidgetId = null
  },
  APPLY_FILTER(state, { filterId, values }) {
    if (values.length) state.appliedFilters[filterId] = [...values]
    else delete state.appliedFilters[filterId]
  },
  SET_FILTER_OPTIONS(state, { filterId, values }) {
    state.filterOptions[filterId] = {
      ...(state.filterOptions[filterId] ?? emptyOptions()),
      ...values,
    }
  },
  SET_REFRESHING(state, value) {
    state.refreshing = value
  },
}

export const filterActions = {
  selectFilter({ commit }, filterId) {
    commit('SELECT_FILTER', filterId)
  },
  async fetchFilters({ state, commit }) {
    const request = dashboardRequest(state)
    commit('INVALIDATE_FILTER_FETCH')
    const generation = state.filterFetchGeneration
    const { data } = await FilterService(this.$client).fetchAll(request.id)
    if (
      !isCurrent(state, request) ||
      generation !== state.filterFetchGeneration
    )
      return
    commit('SET_FILTERS', data)
    for (const filter of data) commit('INVALIDATE_FILTER_OPTIONS', filter.id)
    return data
  },
  async createFilter({ state, commit }, values) {
    const request = dashboardRequest(state)
    const { data } = await FilterService(this.$client).create(
      request.id,
      values
    )
    if (!isCurrent(state, request)) return data
    commit('INVALIDATE_FILTER_FETCH')
    commit('UPSERT_FILTER', data)
    commit('SELECT_FILTER', data.id)
    return data
  },
  async updateFilter({ state, commit, dispatch }, { filterId, values }) {
    const request = dashboardRequest(state)
    commit('INVALIDATE_FILTER_MUTATION', filterId)
    const generation = state.filterMutationGenerations[filterId]
    const { data } = await FilterService(this.$client).update(filterId, values)
    if (
      !isCurrent(state, request) ||
      generation !== state.filterMutationGenerations[filterId] ||
      !state.filters.some((filter) => filter.id === filterId)
    )
      return
    commit('INVALIDATE_FILTER_FETCH')
    commit('INVALIDATE_FILTER_OPTIONS', filterId)
    commit('UPSERT_FILTER', data)
    await dispatch('refreshWidgets')
    return data
  },
  async deleteFilter({ state, commit, dispatch }, filterId) {
    const request = dashboardRequest(state)
    commit('INVALIDATE_FILTER_MUTATION', filterId)
    await FilterService(this.$client).delete(filterId)
    if (!isCurrent(state, request)) return
    commit('INVALIDATE_FILTER_FETCH')
    commit('INVALIDATE_FILTER_OPTIONS', filterId)
    commit('DELETE_FILTER', filterId)
    await dispatch('refreshWidgets')
  },
  async handleFiltersUpdated({ dispatch }) {
    await dispatch('fetchFilters')
    await dispatch('refreshWidgets')
  },
  async applyFilter({ state, commit, dispatch }, { filterId, values }) {
    const filter = state.filters.find((f) => f.id === filterId)
    if (!filter) return
    const normalized =
      filter.mode === 'input'
        ? values.slice(0, 1).map((value) => value.trim())
        : values
    commit('APPLY_FILTER', {
      filterId,
      values: normalized.filter((value) => value !== ''),
    })
    await dispatch('refreshWidgets')
  },
  async fetchFilterOptions(
    { state, commit },
    { filterId, search = '', more = false, selected } = {}
  ) {
    const filter = state.filters.find((f) => f.id === filterId)
    if (!filter || filter.mode !== 'dropdown') return
    const request = dashboardRequest(state)
    const previous = state.filterOptions[filterId] ?? emptyOptions()
    if (more && (previous.loading || previous.next === null)) return
    commit('INVALIDATE_FILTER_OPTIONS', filterId)
    const generation = state.filterOptionGenerations[filterId]
    const current = () =>
      isCurrent(state, request) &&
      generation === state.filterOptionGenerations[filterId] &&
      state.filters.some((f) => f.id === filterId)
    const requestedValues = [
      ...new Set(selected ?? state.appliedFilters[filterId] ?? []),
    ]
    commit('SET_FILTER_OPTIONS', {
      filterId,
      values: {
        loading: true,
        error: false,
        search,
        ...(more ? {} : { results: [], next: null }),
      },
    })
    try {
      const { data } = await FilterService(this.$client).options(filterId, {
        search,
        selected: requestedValues,
        ...(more ? { after: previous.next } : {}),
      })
      if (!current()) return
      commit('SET_FILTER_OPTIONS', {
        filterId,
        values: {
          results: more
            ? [...new Set([...previous.results, ...data.results])]
            : data.results,
          next: data.next,
          unavailable: requestedValues.filter(
            (value) => !data.available.includes(value)
          ),
          loading: false,
          error: false,
        },
      })
    } catch (error) {
      if (!current()) return
      // A failed request never establishes that a selected value disappeared.
      commit('SET_FILTER_OPTIONS', {
        filterId,
        values: { loading: false, error: true },
      })
    }
  },
  async refresh({ state, commit, dispatch }) {
    if (state.refreshing) return
    const request = dashboardRequest(state)
    commit('SET_REFRESHING', true)
    try {
      await Promise.allSettled([
        dispatch('refreshWidgets'),
        ...state.filters
          .filter((f) => f.mode === 'dropdown')
          .map((f) => dispatch('fetchFilterOptions', { filterId: f.id })),
      ])
    } finally {
      if (isCurrent(state, request)) commit('SET_REFRESHING', false)
    }
  },
}

export const filterGetters = {
  getFilters: (state) => state.filters,
  getSelectedFilter: (state) =>
    state.filters.find((f) => f.id === state.selectedFilterId),
  getAppliedFilterValues: (state) => (filterId) =>
    state.appliedFilters[filterId] ?? [],
  getFilterOptions: (state) => (filterId) =>
    state.filterOptions[filterId] ?? emptyOptions(),
  isRefreshing: (state) => state.refreshing,
}
