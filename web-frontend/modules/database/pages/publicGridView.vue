<template>
  <div>
    <Notifications></Notifications>
    <div class="grid-view__public-shared-page">
      <Table
        :database="database"
        :table="table"
        :fields="fields || startingFields"
        :primary="primary || startingPrimary"
        :view="view"
        :read-only="true"
        :table-loading="false"
        :store-prefix="'page/'"
      ></Table>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Notifications from '@baserow/modules/core/components/notifications/Notifications'
import Table from '@baserow/modules/database/components/table/Table'
import GridService from '@baserow/modules/database/services/view/grid'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import { PUBLIC_PLACEHOLDER_ENTITY_ID } from '@baserow/modules/database/utils/constants'

export default {
  components: { Notifications, Table },
  /**
   * Fetches and prepares all the table, field and view data for the provided
   * public grid view.
   */
  async asyncData({ store, params, error, app }) {
    try {
      const viewSlug = params.slug
      await store.dispatch('page/view/grid/setPublic', true)
      const { data } = await GridService(app.$client).fetchPublicViewInfo(
        viewSlug
      )

      const { applications } = await store.dispatch('application/forceSetAll', {
        applications: [
          {
            id: PUBLIC_PLACEHOLDER_ENTITY_ID,
            type: DatabaseApplicationType.getType(),
            tables: [{ id: PUBLIC_PLACEHOLDER_ENTITY_ID }],
          },
        ],
      })
      const database = applications[0]
      const table = database.tables[0]
      await store.dispatch('table/forceSelect', { database, table })

      const { primary, fields } = await store.dispatch('field/forceSetFields', {
        fields: data.fields,
      })

      // We must manually set the filters disabled because it should always be false in
      // this case and it's not provided by the backend.
      data.view.filters_disabled = false
      data.view.filter_type = 'AND'
      const { view } = await store.dispatch('view/forceCreate', {
        data: data.view,
      })
      await store.dispatch('view/select', view)

      // It might be possible that the view also has some stores that need to be
      // filled with initial data, so we're going to call the fetch function here.
      const type = app.$registry.get('view', view.type)
      await type.fetch({ store }, view, fields, primary, 'page/')
      return {
        database,
        table,
        view,
        startingFields: fields,
        startingPrimary: primary,
      }
    } catch (e) {
      if (e.response && e.response.status === 404) {
        return error({ statusCode: 404, message: 'View not found.' })
      } else {
        return error({ statusCode: 500, message: 'Error loading view.' })
      }
    }
  },
  head() {
    return {
      title: this.view.name || '',
    }
  },
  computed: {
    ...mapGetters({
      primary: 'field/getPrimary',
      fields: 'field/getAll',
    }),
  },
  mounted() {
    if (!this.$env.DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS) {
      this.$realtime.connect(true, true)
      this.$realtime.subscribe('view', { slug: this.$route.params.slug })
    }
  },
  beforeDestroy() {
    if (!this.$env.DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS) {
      this.$realtime.subscribe(null)
      this.$realtime.disconnect()
    }
  },
}
</script>
