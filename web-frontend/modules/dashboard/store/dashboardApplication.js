export const state = () => ({
  editMode: false,
})

export const mutations = {
  RESET(state) {
    state.editMode = false
  },
  TOGGLE_EDIT_MODE(state) {
    state.editMode = !state.editMode
  },
}

export const actions = {
  reset({ commit }) {
    commit('RESET')
  },
  toggleEditMode({ commit }) {
    commit('TOGGLE_EDIT_MODE')
  },
}

export const getters = {
  isEditMode(state) {
    return state.editMode
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
