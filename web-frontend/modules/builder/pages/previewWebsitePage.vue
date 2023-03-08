<template>
  <PageContent
    :application="application"
    :path="path"
    :page="page"
    :params="params"
  />
</template>

<script>
import PageContent from '@baserow/modules/builder/components/PageContent'
import publicSiteService from '@baserow/modules/builder/services/builderApplication.js'
import { resolveApplicationRoute } from '@baserow/modules/builder/utils/routing'

export default {
  components: { PageContent },
  async asyncData(context) {
    let application

    try {
      application = await publicSiteService(context.$client).fetchById(
        context.route.params.id
      )
    } catch (e) {
      return context.error({
        statusCode: 404,
        message: 'Application not found.',
      })
    }

    const found = resolveApplicationRoute(
      application,
      context.route.params.pathMatch
    )
    // Handle 404
    if (!found) {
      return context.error({
        statusCode: 404,
        message: 'Page not found.',
      })
    }

    const [page, path, params] = found

    return {
      application,
      page,
      path,
      params,
    }
  },
}
</script>
