import { mapGetters } from 'vuex'
import applicationContextMixin from '@baserow/modules/builder/mixins/applicationContext'

export default {
  mixins: [applicationContextMixin],
  computed: {
    dataSources() {
      return this.$store.getters['dataSource/getPageDataSources'](this.page)
    },
    availableDataSources() {
      return this.dataSources.filter(
        (dataSource) =>
          dataSource.type &&
          this.$registry.get('service', dataSource.type).returnsList
      )
    },
    selectedDataSource() {
      if (!this.values.data_source_id) {
        return null
      }
      return this.$store.getters['dataSource/getPageDataSourceById'](
        this.page,
        this.values.data_source_id
      )
    },
    selectedDataSourceType() {
      if (!this.selectedDataSource || !this.selectedDataSource.type) {
        return null
      }
      return this.$registry.get('service', this.selectedDataSource.type)
    },
    maxItemPerPage() {
      if (!this.selectedDataSourceType) {
        return 20
      }
      return this.selectedDataSourceType.maxResultLimit
    },
    ...mapGetters({
      element: 'element/getSelected',
    }),
  },
  watch: {
    'dataSources.length'(newValue, oldValue) {
      if (this.values.data_source_id && oldValue > newValue) {
        if (
          !this.dataSources.some(({ id }) => id === this.values.data_source_id)
        ) {
          // Remove the data_source_id if the related dataSource has been deleted.
          this.values.data_source_id = null
        }
      }
    },
  },
}
