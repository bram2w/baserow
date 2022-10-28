import RolesService from '@baserow/modules/core/services/roles'

const appendRoleTranslations = (roles, registry) => {
  const translationMap = Object.values(
    registry.getAll('permissionManager')
  ).reduce(
    (translations, manager) => ({
      ...translations,
      ...manager.getRolesTranslations(),
    }),
    {}
  )
  return roles.map((role) => {
    if (translationMap[role.uid]) {
      return {
        uid: role.uid,
        description: translationMap[role.uid].description,
        name: translationMap[role.uid].name,
      }
    }
    return role
  })
}

const state = () => ({
  roles: [],
})

const mutations = {
  SET_ROLES(state, roles) {
    state.roles = roles
  },
}

const actions = {
  async fetchRoles({ commit }, group) {
    const { data } = await RolesService(this.$client, this.app.$hasFeature).get(
      group
    )
    const translatedRoles = appendRoleTranslations(data, this.app.$registry)
    commit('SET_ROLES', translatedRoles)
  },
}

const getters = {
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
