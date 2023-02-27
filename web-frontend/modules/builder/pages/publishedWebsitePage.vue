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
import publicSiteService from '@baserow/modules/builder/services/builderApplication'
import { resolveApplicationRoute } from '@baserow/modules/builder/utils/routing'

export default {
  components: { PageContent },
  async asyncData(context) {
    const host = process.server
      ? context.req.headers.host
      : window.location.host
    const hostname = new URL(`http://${host}`).hostname
    let application

    try {
      application = await publicSiteService(context.$client).fetchByHostname(
        hostname
      )
    } catch (e) {
      return context.error({
        statusCode: 404,
        message: 'Domain not found.',
      })
    }

    const found = resolveApplicationRoute(application, context.route.path)
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
