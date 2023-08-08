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
  async asyncData({ store, params, error, $registry, ...rest }) {
    const builderId = parseInt(params.builderId)
    const pageId = parseInt(params.pageId)

    const data = { panelWidth: 360 }

    try {
      await store.dispatch('element/clearAll')
      const { builder, page } = await store.dispatch('page/selectById', {
        builderId,
        pageId,
      })
      data.builder = builder
      data.page = page

      await store.dispatch('workspace/selectById', builder.workspace.id)

      await store.dispatch('dataSource/fetch', {
        page,
      })

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

      await store.dispatch('element/fetch', { page })
    } catch (e) {
      // In case of a network error we want to fail hard.
      if (e.response === undefined && !(e instanceof StoreItemLookupError)) {
        throw e
      }

      return error({ statusCode: 404, message: 'page not found.' })
    }

    return data
  },
}
</script>
