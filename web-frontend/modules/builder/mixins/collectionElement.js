import { mapActions, mapGetters } from 'vuex'
import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'
import { notifyIf } from '@baserow/modules/core/utils/error'
import _ from 'lodash'

export default {
  data() {
    return {
      currentOffset: 0,
      errorNotified: false,
      resetTimeout: null,
    }
  },
  computed: {
    ...mapGetters({
      getLoading: 'elementContent/getLoading',
      getHasMorePage: 'elementContent/getHasMorePage',
      getElementContent: 'elementContent/getElementContent',
      getReset: 'elementContent/getReset',
      getPageDataSourceById: 'dataSource/getPageDataSourceById',
    }),
    reset() {
      return this.getReset(this.element)
    },
    dataSource() {
      if (!this.element.data_source_id) {
        return null
      }
      return this.getPageDataSourceById(this.page, this.element.data_source_id)
    },
    dataSourceType() {
      if (!this.dataSource) {
        return null
      }
      return this.$registry.get('service', this.dataSource.type)
    },
    elementContent() {
      return this.getElementContent(this.element, this.applicationContext)
    },
    hasMorePage() {
      return this.getHasMorePage(this.element)
    },
    contentLoading() {
      return this.getLoading(this.element) && !this.elementIsInError
    },
    dispatchContext() {
      return DataProviderType.getAllDataSourceDispatchContext(
        this.$registry.getAll('builderDataProvider'),
        this.applicationContext
      )
    },
    elementIsInError() {
      return this.elementType.isInError({
        page: this.page,
        element: this.element,
        builder: this.builder,
      })
    },
  },
  watch: {
    reset() {
      this.debouncedReset()
    },
    'element.schema_property'(newValue, oldValue) {
      if (newValue) {
        this.debouncedReset()
      }
    },
    'element.data_source_id'() {
      this.debouncedReset()
    },
    'element.items_per_page'() {
      this.debouncedReset()
    },
    dispatchContext: {
      handler(newValue, prevValue) {
        if (!_.isEqual(newValue, prevValue)) {
          this.debouncedReset()
        }
      },
      deep: true,
    },
  },
  async mounted() {
    if (!this.elementIsInError && this.elementType.fetchAtLoad) {
      // This fetch is necessary when we duplicate the collection element as
      // the initial load from the data provider has already happened.
      // It won't be executed by the store when the data provider has already loaded
      // the data because the range is the same in which case only the `currentOffset`
      // is updated.
      await this.fetchContent([0, this.element.items_per_page])
    }
  },
  methods: {
    ...mapActions({
      fetchElementContent: 'elementContent/fetchElementContent',
      clearElementContent: 'elementContent/clearElementContent',
    }),
    debouncedReset() {
      clearTimeout(this.resetTimeout)
      this.resetTimeout = setTimeout(() => {
        this.errorNotified = false
        this.currentOffset = 0
        this.loadMore(true)
      }, 500)
    },
    async fetchContent(range, replace) {
      if (!this.canFetch()) {
        return
      }
      try {
        await this.fetchElementContent({
          page: this.page,
          element: this.element,
          dataSource: this.dataSource,
          data: this.dispatchContext,
          range,
          replace,
        })
        this.currentOffset += this.element.items_per_page
      } catch (error) {
        // We need to only launch one toast error message per element,
        // not one per element fetch, or we can end up with many error
        // toasts per element sharing a datasource.
        if (!this.errorNotified) {
          this.errorNotified = true
          notifyIf(error)
        }
      }
    },
    async loadMore(replace = false) {
      await this.fetchContent(
        [this.currentOffset, this.element.items_per_page],
        replace
      )
    },
    /** Overrides this if you want to prevent data fetching */
    canFetch() {
      return true
    },
  },
}
