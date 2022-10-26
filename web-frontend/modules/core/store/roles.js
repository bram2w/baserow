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

function appendRoleTranslations(roles, registry, i18n) {
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
    const translations = Object.keys(translationMap[role.uid]).reduce(
      (translations, key) => ({
        ...translations,
        [key]: i18n.t(translationMap[role.uid][key]),
      }),
      {}
    )
    return {
      ...role,
      ...translations,
    }
  })
}

export default ({ registry, i18n }) => {
  const state = () => ({
    roles: appendRoleTranslations(defaultRoles, registry, i18n), // TODO set to [] when endpoint is implemented
  })

  const mutations = {
    SET_ROLES(state, roles) {
      state.roles = appendRoleTranslations(roles, registry, i18n)
    },
  }

  const actions = {
    fetchRoles() {
      // TODO implement once endpoint exists
      return null
    },
  }

  const getters = {
    getAllRoles(state) {
      return state.roles
    },
  }

  return {
    namespaced: true,
    state,
    getters,
    actions,
    mutations,
  }
}
