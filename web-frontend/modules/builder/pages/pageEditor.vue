<template>
  <div class="page-editor">
    <PageHeader :page="page" />
    <div class="layout__col-2-2 page-editor__content">
      <div :style="{ width: `calc(100% - ${panelWidth}px)` }">
        <PagePreview />
      </div>
      <div class="page-editor__side-panel">
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
import RuntimeFormulaContext from '@baserow/modules/core/runtimeFormulaContext'

export default {
  name: 'PageEditor',
  components: { PagePreview, PageHeader, PageSidePanels },
  provide() {
    return { builder: this.builder, page: this.page, mode: 'editing' }
  },
  /**
   * When the user leaves to another page we want to unselect the selected page. This
   * way it will not be highlighted the left sidebar.
   */
  beforeRouteLeave(to, from, next) {
    this.$store.dispatch('page/unselect')
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
      ])

      const runtimeFormulaContext = new RuntimeFormulaContext(
        $registry.getAll('builderDataProvider'),
        {
          builder,
          page,
          mode: 'editing',
        }
      )

      // Initialize all data provider contents
      await runtimeFormulaContext.initAll()

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
    dataSources() {
      return this.$store.getters['dataSource/getPageDataSources'](this.page)
    },
    runtimeFormulaContext() {
      return new RuntimeFormulaContext(
        this.$registry.getAll('builderDataProvider'),
        {
          builder: this.builder,
          page: this.page,
          mode: 'editing',
        }
      )
    },
    backendContext() {
      return this.runtimeFormulaContext.getAllBackendContext()
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
            data: this.backendContext,
          }
        )
      },
    },
    backendContext: {
      deep: true,
      /**
       * Update data source content on backend context changes
       */
      handler(newBackendContext) {
        this.$store.dispatch(
          'dataSourceContent/debouncedFetchPageDataSourceContent',
          {
            page: this.page,
            data: newBackendContext,
          }
        )
      },
    },
  },
}
</script>
