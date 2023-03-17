<template>
  <div>
    <PageHeader />
    <div class="layout__col-2-2 content" @click.self="unselectElement">
      <div class="page__wrapper">
        <PagePreview />
      </div>
    </div>
  </div>
</template>

<script>
import { StoreItemLookupError } from '@baserow/modules/core/errors'
import PageHeader from '@baserow/modules/builder/components/page/PageHeader'
import PagePreview from '@baserow/modules/builder/components/page/PagePreview'

export default {
  name: 'Page',
  components: { PagePreview, PageHeader },
  /**
   * When the user leaves to another page we want to unselect the selected page. This
   * way it will not be highlighted the left sidebar.
   */
  beforeRouteLeave(to, from, next) {
    this.$store.dispatch('page/unselect')
    next()
  },

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
  methods: {
    unselectElement() {
      this.$store.dispatch('element/select', { element: null })
    },
  },
}
</script>
