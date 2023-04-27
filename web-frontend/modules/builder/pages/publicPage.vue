<template>
  <PublicPage :builder="builder" :page="page" :path="path" :params="params" />
</template>

<script>
import PublicPage from '@baserow/modules/builder/components/page/PublicPage'
import { resolveApplicationRoute } from '@baserow/modules/builder/utils/routing'

export default {
  components: { PublicPage },

  async asyncData(context) {
    let builder = context.store.getters['publicBuilder/getBuilder']

    if (!builder) {
      try {
        const builderId = context.route.params.builderId
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

    return {
      builder,
      page,
      path,
      params,
    }
  },
}
</script>
