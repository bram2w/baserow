// TODO remove once endpoint is implemented
const defaultRoles = [
  {
    uid: 'ADMIN',
    name: 'permission.admin',
    description: 'permission.adminDescription',
  },
  {
    uid: 'MEMBER',
    name: 'permission.member',
    description: 'permission.memberDescription',
  },
]

export const state = () => ({
  roles: defaultRoles, // TODO set to [] when endpoint is implemented
})

export const mutations = {
  SET_ROLES(state, roles) {
    state.roles = roles
  },
}

export const actions = {
  fetchRoles() {
    // TODO implement once endpoint exists
    return null
  },
}

export const getters = {
  getAllRoles(state) {
    return state.roles
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
