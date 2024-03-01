<template>
  <div class="page-editor">
    <PageHeader :page="page" />
    <div class="layout__col-2-2 page-editor__content">
      <div :style="{ width: `calc(100% - ${panelWidth}px)` }">
        <PagePreview />
      </div>
      <div
        class="page-editor__side-panel"
        :style="{ width: `${panelWidth}px` }"
      >
        <PageSidePanels />
      </div>
    </div>
  </div>
</template>

<script>
import { StoreItemLookupError } from '@baserow/modules/core/errors'
import PageHeader from '@baserow/modules/builder/components/page/header/PageHeader'
import PagePreview from '@baserow/modules/builder/components/page/PagePreview'
import PageSidePanels from '@baserow/modules/builder/components/page/PageSidePanels'
import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import _ from 'lodash'

const mode = 'editing'

export default {
  name: 'PageEditor',
  components: { PagePreview, PageHeader, PageSidePanels },
  provide() {
    return {
      builder: this.builder,
      page: this.page,
      mode,
      formulaComponent: ApplicationBuilderFormulaInputGroup,
    }
  },
  /**
   * When the route isupdate we want to unselect the element
   */
  beforeRouteUpdate(to, from, next) {
    // Unselect previously selected element
    this.$store.dispatch(
      'element/select',
      {
        element: null,
      },
      { root: true }
    )
    if (from.params.builderId !== to.params?.builderId) {
      // When we switch from one application to another we want to logoff the current
      // user
      this.$store.dispatch('userSourceUser/logoff')
    }
    next()
  },
  /**
   * When the user leaves to another page we want to unselect the selected page. This
   * way it will not be highlighted the left sidebar.
   */
  beforeRouteLeave(to, from, next) {
    this.$store.dispatch('page/unselect')
    // Unselect previously selected element
    this.$store.dispatch(
      'element/select',
      {
        element: null,
      },
      { root: true }
    )
    this.$store.dispatch('userSourceUser/logoff')
    next()
  },
  layout: 'app',
  async asyncData({ store, params, error, $registry }) {
    const builderId = parseInt(params.builderId)
    const pageId = parseInt(params.pageId)

    const data = { panelWidth: 360 }

    try {
      const builder = await store.dispatch('application/selectById', builderId)

      const page = store.getters['page/getById'](builder, pageId)

      await store.dispatch('workspace/selectById', builder.workspace.id)

      await Promise.all([
        store.dispatch('dataSource/fetch', {
          page,
        }),
        store.dispatch('element/fetch', { page }),
        store.dispatch('workflowAction/fetch', { page }),
      ])

      await DataProviderType.initAll($registry.getAll('builderDataProvider'), {
        builder,
        page,
        mode,
      })

      // And finally select the page to display it
      await store.dispatch('page/selectById', {
        builder,
        pageId,
      })

      data.builder = builder
      data.page = page
    } catch (e) {
      // In case of a network error we want to fail hard.
      if (e.response === undefined && !(e instanceof StoreItemLookupError)) {
        throw e
      }

      return error({ statusCode: 404, message: 'page not found.' })
    }

    return data
  },
  computed: {
    applicationContext() {
      return {
        builder: this.builder,
        page: this.page,
        mode,
      }
    },
    dataSources() {
      return this.$store.getters['dataSource/getPageDataSources'](this.page)
    },
    dispatchContext() {
      return DataProviderType.getAllDispatchContext(
        this.$registry.getAll('builderDataProvider'),
        this.applicationContext
      )
    },
  },
  watch: {
    dataSources: {
      deep: true,
      /**
       * Update data source content on data source configuration changes
       */
      handler() {
        this.$store.dispatch(
          'dataSourceContent/debouncedFetchPageDataSourceContent',
          {
            page: this.page,
            data: this.dispatchContext,
          }
        )
      },
    },
    dispatchContext: {
      deep: true,
      /**
       * Update data source content on backend context changes
       */
      handler(newDispatchContext, oldDispatchContext) {
        if (!_.isEqual(newDispatchContext, oldDispatchContext)) {
          this.$store.dispatch(
            'dataSourceContent/debouncedFetchPageDataSourceContent',
            {
              page: this.page,
              data: newDispatchContext,
            }
          )
        }
      },
    },
  },
}
</script>
