<template>
  <div>PAGE</div>
</template>

<script>
import { StoreItemLookupError } from '@baserow/modules/core/errors'

export default {
  name: 'Page',
  layout: 'app',

  async asyncData({ store, params, error }) {
    const builderId = parseInt(params.builderId)
    const pageId = parseInt(params.pageId)

    const data = {}

    try {
      const { builder, page } = await store.dispatch('page/selectById', {
        builderId,
        pageId,
      })
      await store.dispatch('group/selectById', builder.group.id)
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
}
</script>
