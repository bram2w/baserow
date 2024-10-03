<template>
  <div v-if="page" :key="page.id" class="page-template">
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
import PageHeader from '@baserow/modules/builder/components/page/header/PageHeader'
import PagePreview from '@baserow/modules/builder/components/page/PagePreview'
import PageSidePanels from '@baserow/modules/builder/components/page/PageSidePanels'
import ApplicationBuilderFormulaInput from '@baserow/modules/builder/components/ApplicationBuilderFormulaInput'
import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'
import _ from 'lodash'

const mode = 'editing'

export default {
  name: 'PageTemplate',
  components: { PagePreview, PageHeader, PageSidePanels },
  provide() {
    return {
      workspace: this.workspace,
      builder: this.builder,
      page: this.page,
      mode,
      formulaComponent: ApplicationBuilderFormulaInput,
      applicationContext: { builder: this.builder, page: this.page, mode },
    }
  },
  props: {
    workspace: {
      type: Object,
      required: true,
    },
    builder: {
      type: Object,
      required: true,
    },
    page: {
      type: Object,
      required: true,
    },
    mode: {
      type: String,
      required: true,
    },
  },
  data() {
    return { panelWidth: 300 }
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
      return DataProviderType.getAllDataSourceDispatchContext(
        this.$registry.getAll('builderDataProvider'),
        this.applicationContext
      )
    },
  },
  watch: {
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
              mode: this.mode,
            }
          )
        }
      },
    },
  },
}
</script>
