import { mapActions, mapGetters } from 'vuex'
import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'
import { notifyIf } from '@baserow/modules/core/utils/error'
import _ from 'lodash'

export default {
  data() {
    return {
      // The first page has been loaded by the data provider at page load already
      currentOffset: this.element.items_per_page,
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
    elementContent() {
      if (
        !this.element.data_source_id ||
        !this.getElementContent(this.element)
      ) {
        return []
      }

      return this.getElementContent(this.element)
    },
    hasMorePage() {
      return this.getHasMorePage(this.element)
    },
    contentLoading() {
      return this.getLoading(this.element)
    },
    dispatchContext() {
      return DataProviderType.getAllDataSourceDispatchContext(
        this.$registry.getAll('builderDataProvider'),
        this.applicationContext
      )
    },
  },
  watch: {
    reset() {
      this.debouncedReset()
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
      immediate: true,
    },
  },
  async mounted() {
    if (this.element.data_source_id) {
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
      try {
        await this.fetchElementContent({
          element: this.element,
          dataSource: this.dataSource,
          data: this.dispatchContext,
          range,
          replace,
        })
      } catch (error) {
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

      this.currentOffset += this.element.items_per_page
    },
  },
}
