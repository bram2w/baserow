// import { set } from 'vue'

import GroupService from '@/services/group'

export const state = () => ({
  loaded: false,
  loading: false,
  items: []
})

export const mutations = {
  SET_LOADED(state, loaded) {
    state.loaded = loaded
  },
  SET_LOADING(state, loading) {
    state.loading = loading
  },
  SET_ITEMS(state, items) {
    state.items = items
  },
  ADD_ITEM(state, item) {
    state.items.push(item)
  },
  UPDATE_ITEM(state, values) {
    const index = state.items.findIndex(item => item.id === values.id)
    Object.assign(state.items[index], state.items[index], values)
  },
  DELETE_ITEM(state, id) {
    const index = state.items.findIndex(item => item.id === id)
    state.items.splice(index, 1)
  }
}

export const actions = {
  loadAll({ state, dispatch }) {
    if (!state.loaded && !state.loading) {
      dispatch('fetchAll')
    }
  },
  fetchAll({ commit }) {
    commit('SET_LOADING', true)

    return GroupService.fetchAll()
      .then(({ data }) => {
        commit('SET_LOADED', true)
        commit('SET_ITEMS', data)
      })
      .catch(() => {
        commit('SET_ITEMS', [])
      })
      .then(() => {
        commit('SET_LOADING', false)
      })
  },
  create({ commit }, values) {
    return GroupService.create(values).then(({ data }) => {
      commit('ADD_ITEM', data)
    })
  },
  update({ commit }, { id, values }) {
    return GroupService.update(id, values).then(({ data }) => {
      commit('UPDATE_ITEM', data)
    })
  },
  delete({ commit }, id) {
    return GroupService.delete(id).then(() => {
      console.log(id)
      commit('DELETE_ITEM', id)
    })
  }
}

export const getters = {
  isLoaded(state) {
    return state.loaded
  },
  isLoading(state) {
    return state.loading
  }
}
