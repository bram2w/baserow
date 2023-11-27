import { mapGetters } from 'vuex'

export default {
  computed: {
    ...mapGetters({
      isPublic: 'page/view/public/getIsPublic',
    }),
    filterTypes() {
      const filterTypes = this.$registry.getAll('viewFilter')
      const allowedTypes = Object.keys(filterTypes)
        .filter(
          (key) => !this.isPublic || filterTypes[key].isAllowedInPublicViews()
        )
        .reduce((obj, key) => {
          return {
            ...obj,
            [key]: filterTypes[key],
          }
        }, {})
      return allowedTypes
    },
  },
}
