<template>
  <div>
    <Toasts></Toasts>
    <PageContent
      :page="page"
      :path="path"
      :params="params"
      :elements="elements"
    />
  </div>
</template>

<script>
import PageContent from '@baserow/modules/builder/components/page/PageContent'
import { resolveApplicationRoute } from '@baserow/modules/builder/utils/routing'

import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'
import Toasts from '@baserow/modules/core/components/toasts/Toasts'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import _ from 'lodash'

export default {
  components: { PageContent, Toasts },
  provide() {
    return {
      builder: this.builder,
      page: this.page,
      mode: this.mode,
      formulaComponent: ApplicationBuilderFormulaInputGroup,
    }
  },
  middleware: ['userSourceAuthentication'],
  async asyncData({ store, params, error, $registry, app, req }) {
    let mode = 'public'
    const builderId = parseInt(params.builderId, 10)

    // We have a builderId parameter in the path so it's a preview
    if (builderId) {
      mode = 'preview'
    }

    let builder = store.getters['application/getSelected']

    if (!builder || builderId !== builder.id) {
      try {
        if (builderId) {
          // We have the builderId in the params so this is a preview
          // Must fetch the builder instance by this Id.
          await store.dispatch('publicBuilder/fetchById', {
            builderId,
          })
          builder = await store.dispatch('application/selectById', builderId)
        } else {
          // We don't have the builderId so it's a public page.
          // Must fetch the builder instance by domain name.
          const host = process.server ? req.headers.host : window.location.host
          const domain = new URL(`http://${host}`).hostname

          const { id: receivedBuilderId } = await store.dispatch(
            'publicBuilder/fetchByDomain',
            {
              domain,
            }
          )
          builder = await store.dispatch(
            'application/selectById',
            receivedBuilderId
          )
        }
      } catch (e) {
        return error({
          statusCode: 404,
          message: app.i18n.t('publicPage.siteNotFound'),
        })
      }
    }

    const found = resolveApplicationRoute(builder.pages, params.pathMatch)

    // Handle 404
    if (!found) {
      return error({
        statusCode: 404,
        message: app.i18n.t('publicPage.pageNotFound'),
      })
    }

    const [pageFound, path, pageParamsValue] = found

    const page = await store.getters['page/getById'](builder, pageFound.id)

    await Promise.all([
      store.dispatch('dataSource/fetchPublished', {
        page,
      }),
      store.dispatch('element/fetchPublished', { page }),
      store.dispatch('workflowAction/fetchPublished', { page }),
    ])

    await DataProviderType.initAll($registry.getAll('builderDataProvider'), {
      builder,
      page,
      pageParamsValue,
      mode,
    })

    // And finally select the page to display it
    await store.dispatch('page/selectById', {
      builder,
      pageId: pageFound.id,
    })

    return {
      builder,
      page,
      path,
      params,
      mode,
    }
  },
  head() {
    return {
      titleTemplate: '',
      title: this.page.name,
      bodyAttrs: {
        class: 'public-page',
      },
    }
  },
  computed: {
    elements() {
      return this.$store.getters['element/getRootElements'](this.page)
    },
    applicationContext() {
      return {
        builder: this.builder,
        page: this.page,
        pageParamsValue: this.params,
        mode: this.mode,
      }
    },
    dispatchContext() {
      return DataProviderType.getAllDispatchContext(
        this.$registry.getAll('builderDataProvider'),
        this.applicationContext
      )
    },
  },
  watch: {
    dispatchContext: {
      deep: true,
      /**
       * Update data source content on dispatch context changes
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
