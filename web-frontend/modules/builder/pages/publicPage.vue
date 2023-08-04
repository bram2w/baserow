<template>
  <PageContent
    :page="page"
    :path="path"
    :params="params"
    :elements="elements"
  />
</template>

<script>
import PageContent from '@baserow/modules/builder/components/page/PageContent'
import { resolveApplicationRoute } from '@baserow/modules/builder/utils/routing'
import RuntimeFormulaContext from '@baserow/modules/core/runtimeFormulaContext'
import { mapGetters } from 'vuex'

export default {
  components: { PageContent },
  provide() {
    return { builder: this.builder, mode: this.mode }
  },
  async asyncData(context) {
    let builder = context.store.getters['publicBuilder/getBuilder']
    let mode = 'public'
    const builderId = context.route.params.builderId

    if (!builder) {
      try {
        if (builderId) {
          // We have the builderId in the params so this is a preview
          // Must fetch the builder instance by this Id.

          await context.store.dispatch('publicBuilder/fetchById', {
            builderId,
          })
        } else {
          // We don't have the builderId so it's a public page.
          // Must fetch the builder instance by domain name.
          const host = process.server
            ? context.req.headers.host
            : window.location.host
          const domain = new URL(`http://${host}`).hostname

          await context.store.dispatch('publicBuilder/fetchByDomain', {
            domain,
          })
        }
        builder = context.store.getters['publicBuilder/getBuilder']
      } catch (e) {
        return context.error({
          statusCode: 404,
          message: context.app.i18n.t('publicPage.siteNotFound'),
        })
      }
    }

    if (builderId) {
      mode = 'preview'
    }

    const found = resolveApplicationRoute(
      builder.pages,
      context.route.params.pathMatch
    )

    // Handle 404
    if (!found) {
      return context.error({
        statusCode: 404,
        message: context.app.i18n.t('publicPage.pageNotFound'),
      })
    }

    const [page, path, params] = found

    await context.store.dispatch('element/clearAll')

    await context.store.dispatch('dataSource/fetchPublished', {
      page,
    })

    const runtimeFormulaContext = new RuntimeFormulaContext(
      context.$registry.getAll('builderDataProvider'),
      {
        builder,
        page,
        pageParamsValue: params,
        mode,
      }
    )

    // Initialize all data provider contents
    await runtimeFormulaContext.initAll()

    await context.store.dispatch('element/fetchPublished', { page })

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
    ...mapGetters({
      elements: 'element/getElements',
    }),
  },
}
</script>
