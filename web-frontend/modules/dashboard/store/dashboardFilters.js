import FilterService from '@baserow/modules/dashboard/services/filter'
import {
  filterHasOptions,
  shouldResetFilterValues,
} from '@baserow/modules/dashboard/utils/filter'
import {
  getSavedFilterValues,
  saveFilterValues,
} from '@baserow/modules/dashboard/utils/filterStorage'

export const filterState = () => ({
  filters: [],
  selectedFilterId: null,
  appliedFilters: {},
  filterValuesRestored: false,
  filterValuesUserId: null,
  filterFetchGeneration: 0,
  filterMutationGenerations: {},
  filterOptionGenerations: {},
  filterOptions: {},
  refreshing: false,
})

const dashboardRequest = (state, rootGetters) => ({
  id: state.dashboardId,
  generation: state.dashboardGeneration,
  userId: rootGetters['auth/getUserId'],
})
const isCurrent = (state, request, rootGetters) =>
  state.dashboardId === request.id &&
  state.dashboardGeneration === request.generation &&
  request.userId === rootGetters['auth/getUserId']
const persistFilterValues = (state, rootGetters) => {
  if (
    !state.filterValuesRestored ||
    state.filterValuesUserId !== rootGetters['auth/getUserId']
  )
    return
  saveFilterValues(
    state.filterValuesUserId,
    state.dashboardId,
    state.filters,
    state.appliedFilters
  )
}
const emptyOptions = () => ({
  results: [],
  labels: {},
  next: null,
  unavailable: [],
  availabilityGeneration: 0,
  loading: false,
  error: false,
  search: '',
  unfilteredOptions: null,
  unfilteredGeneration: null,
  unfilteredLoading: false,
})

export const filterMutations = {
  RESTORE_FILTER_VALUES(state, { userId, selections }) {
    for (const { filterId, values } of selections) {
      state.appliedFilters[filterId] = values
    }
    state.filterValuesRestored = true
    state.filterValuesUserId = userId
  },
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
    const previous = new Map(state.filters.map((filter) => [filter.id, filter]))
    state.filters = filters
    const byId = new Map(filters.map((filter) => [filter.id, filter]))
    for (const id of Object.keys(state.appliedFilters)) {
      const filterId = Number(id)
      const filter = byId.get(filterId)
      if (!filter || shouldResetFilterValues(previous.get(filterId), filter)) {
        delete state.appliedFilters[id]
      }
    }
    if (!byId.has(state.selectedFilterId)) state.selectedFilterId = null
  },
  UPSERT_FILTER(state, filter) {
    const index = state.filters.findIndex((f) => f.id === filter.id)
    if (shouldResetFilterValues(state.filters[index], filter)) {
      delete state.appliedFilters[filter.id]
    }
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
  async fetchFilters({ state, commit, rootGetters }) {
    const request = dashboardRequest(state, rootGetters)
    commit('INVALIDATE_FILTER_FETCH')
    const generation = state.filterFetchGeneration
    const { data } = await FilterService(this.$client).fetchAll(request.id)
    if (
      !isCurrent(state, request, rootGetters) ||
      generation !== state.filterFetchGeneration
    )
      return
    commit('SET_FILTERS', data)
    if (!state.filterValuesRestored) {
      commit('RESTORE_FILTER_VALUES', {
        userId: request.userId,
        selections: getSavedFilterValues(request.userId, request.id, data),
      })
    }
    persistFilterValues(state, rootGetters)
    for (const filter of data) {
      commit('INVALIDATE_FILTER_OPTIONS', filter.id)
      commit('SET_FILTER_OPTIONS', {
        filterId: filter.id,
        values: emptyOptions(),
      })
    }
    return data
  },
  async createFilter({ state, commit, dispatch, rootGetters }, values) {
    const request = dashboardRequest(state, rootGetters)
    const { data } = await FilterService(this.$client).create(
      request.id,
      values
    )
    if (!isCurrent(state, request, rootGetters)) return data
    commit('INVALIDATE_FILTER_FETCH')
    commit('UPSERT_FILTER', data)
    commit('SELECT_FILTER', data.id)
    await dispatch('enterEditMode')
    return data
  },
  async updateFilter(
    { state, commit, dispatch, rootGetters },
    { filterId, values }
  ) {
    const request = dashboardRequest(state, rootGetters)
    commit('INVALIDATE_FILTER_MUTATION', filterId)
    const generation = state.filterMutationGenerations[filterId]
    const { data } = await FilterService(this.$client).update(filterId, values)
    if (
      !isCurrent(state, request, rootGetters) ||
      generation !== state.filterMutationGenerations[filterId] ||
      !state.filters.some((filter) => filter.id === filterId)
    )
      return
    commit('INVALIDATE_FILTER_FETCH')
    commit('INVALIDATE_FILTER_OPTIONS', filterId)
    commit('SET_FILTER_OPTIONS', { filterId, values: emptyOptions() })
    commit('UPSERT_FILTER', data)
    persistFilterValues(state, rootGetters)
    await dispatch('refreshWidgets')
    return data
  },
  async deleteFilter({ state, commit, dispatch, rootGetters }, filterId) {
    const request = dashboardRequest(state, rootGetters)
    commit('INVALIDATE_FILTER_MUTATION', filterId)
    await FilterService(this.$client).delete(filterId)
    if (!isCurrent(state, request, rootGetters)) return
    commit('INVALIDATE_FILTER_FETCH')
    commit('INVALIDATE_FILTER_OPTIONS', filterId)
    commit('DELETE_FILTER', filterId)
    persistFilterValues(state, rootGetters)
    await Promise.all([
      dispatch('fetchNewDataSources', request.id),
      dispatch('refreshWidgets'),
    ])
  },
  async handleFiltersUpdated({ state, dispatch }) {
    const filters = await dispatch('fetchFilters')
    if (filters !== undefined) {
      await Promise.all([
        dispatch('fetchNewDataSources', state.dashboardId),
        dispatch('refreshWidgets'),
      ])
    }
  },
  async applyFilter(
    { state, commit, dispatch, rootGetters },
    { filterId, values }
  ) {
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
    persistFilterValues(state, rootGetters)
    await dispatch('refreshWidgets')
  },
  async fetchFilterOptions(
    { state, commit, rootGetters },
    { filterId, search = '', more = false, selected, useCache = false } = {}
  ) {
    const filter = state.filters.find((f) => f.id === filterId)
    if (!filter || !filterHasOptions(filter)) return
    const request = dashboardRequest(state, rootGetters)
    const previous = state.filterOptions[filterId] ?? emptyOptions()
    if (useCache && !search && !more) {
      // Reopening must not restart an initial load or an explicit Refresh.
      if (previous.unfilteredLoading) {
        if (previous.search !== '') {
          commit('INVALIDATE_FILTER_OPTIONS', filterId)
          commit('SET_FILTER_OPTIONS', {
            filterId,
            values: {
              ...(previous.unfilteredOptions ?? { results: [], next: null }),
              search: '',
              loading: true,
              error: false,
            },
          })
        }
        return
      }
      if (previous.unfilteredOptions) {
        commit('INVALIDATE_FILTER_OPTIONS', filterId)
        commit('SET_FILTER_OPTIONS', {
          filterId,
          values: {
            ...previous.unfilteredOptions,
            search: '',
            loading: false,
            error: false,
          },
        })
        return
      }
      // Keep a failed preload visible; Retry and Refresh explicitly retry it.
      if (previous.error) return
    }
    if (more && (previous.loading || previous.next === null)) return
    commit('INVALIDATE_FILTER_OPTIONS', filterId)
    const generation = state.filterOptionGenerations[filterId]
    const current = () =>
      isCurrent(state, request, rootGetters) &&
      generation === state.filterOptionGenerations[filterId] &&
      state.filters.some((f) => f.id === filterId)
    const cacheCurrent = () =>
      !search &&
      isCurrent(state, request, rootGetters) &&
      state.filters.some((f) => f.id === filterId) &&
      state.filterOptions[filterId]?.unfilteredGeneration === generation
    const displayCurrent = () =>
      current() ||
      (cacheCurrent() && state.filterOptions[filterId].search === '')
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
        ...(!search && !more ? { unfilteredOptions: null } : {}),
        ...(!search
          ? { unfilteredGeneration: generation, unfilteredLoading: true }
          : {}),
      },
    })
    try {
      const { data } = await FilterService(this.$client).options(filterId, {
        search,
        selected: requestedValues,
        ...(more ? { after: previous.next } : {}),
      })
      // An intervening search can replace the visible query while Refresh
      // still fills the unfiltered cache. Configuration resets invalidate both.
      if (!current() && !cacheCurrent()) return
      const results = more
        ? [...new Set([...previous.results, ...data.results])]
        : data.results
      const labels = { ...(more ? previous.labels : {}), ...data.labels }
      const availabilityCurrent =
        generation > state.filterOptions[filterId].availabilityGeneration
      commit('SET_FILTER_OPTIONS', {
        filterId,
        values: {
          ...(cacheCurrent()
            ? {
                unfilteredOptions: { results, labels, next: data.next },
                unfilteredLoading: false,
              }
            : {}),
          ...(availabilityCurrent
            ? {
                unavailable: requestedValues.filter(
                  (value) => !data.available.includes(value)
                ),
                availabilityGeneration: generation,
              }
            : {}),
          ...(displayCurrent()
            ? {
                results,
                labels,
                next: data.next,
                loading: false,
                error: false,
              }
            : {}),
        },
      })
    } catch (error) {
      if (!current() && !cacheCurrent()) return
      // A failed request never establishes that a selected value disappeared.
      commit('SET_FILTER_OPTIONS', {
        filterId,
        values: {
          ...(cacheCurrent() ? { unfilteredLoading: false } : {}),
          ...(displayCurrent() ? { loading: false, error: true } : {}),
        },
      })
    }
  },
  async refresh({ state, commit, dispatch, rootGetters }) {
    if (state.refreshing) return
    const request = dashboardRequest(state, rootGetters)
    commit('SET_REFRESHING', true)
    try {
      await Promise.allSettled([
        dispatch('refreshWidgets'),
        ...state.filters
          .filter(filterHasOptions)
          .map((f) => dispatch('fetchFilterOptions', { filterId: f.id })),
      ])
    } finally {
      if (isCurrent(state, request, rootGetters))
        commit('SET_REFRESHING', false)
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
