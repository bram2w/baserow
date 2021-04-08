<template>
  <Table
    :database="database"
    :table="table"
    :fields="fields"
    :primary="primary"
    :views="views"
    :view="view"
    :table-loading="tableLoading"
    store-prefix="page/"
    @selected-view="selectedView"
  ></Table>
</template>

<script>
import { mapState } from 'vuex'

import Table from '@baserow/modules/database/components/table/Table'
import { StoreItemLookupError } from '@baserow/modules/core/errors'

/**
 * This page component is the skeleton for a table. Depending on the selected view it
 * will load the correct components into the header and body.
 */
export default {
  components: { Table },
  /**
   * When the user leaves to another page we want to unselect the selected table. This
   * way it will not be highlighted the left sidebar.
   */
  beforeRouteLeave(to, from, next) {
    this.$store.dispatch('table/unselect')
    next()
  },
  layout: 'app',
  /**
   * Because there is no hook that is called before the route changes, we need the
   * tableLoading middleware to change the table loading state. This change will get
   * rendered right away. This allows us to have a custom loading animation when
   * switching views.
   */
  middleware: ['tableLoading'],
  /**
   * Prepares all the table, field and view data for the provided database, table and
   * view id.
   */
  async asyncData({ store, params, error, app }) {
    // @TODO figure out why the id's aren't converted to an int in the route.
    const databaseId = parseInt(params.databaseId)
    const tableId = parseInt(params.tableId)
    let viewId = params.viewId ? parseInt(params.viewId) : null
    const data = {}

    // Try to find the table in the already fetched applications by the
    // groupsAndApplications middleware and select that one. By selecting the table, the
    // fields and views are also going to be fetched.
    try {
      const { database, table } = await store.dispatch('table/selectById', {
        databaseId,
        tableId,
      })
      await store.dispatch('group/selectById', database.group.id)
      data.database = database
      data.table = table
    } catch (e) {
      // In case of a network error we want to fail hard.
      if (e.response === undefined && !(e instanceof StoreItemLookupError)) {
        throw e
      }

      return error({ statusCode: 404, message: 'Table not found.' })
    }

    // After selecting the table the fields become available which need to be added to
    // the data.
    data.fields = store.getters['field/getAll']
    data.primary = store.getters['field/getPrimary']
    data.view = undefined

    // Because we do not have a dashboard for the table yet we're going to redirect to
    // the first available view.
    const firstView = store.getters['view/first']
    if (viewId === null && firstView !== null) {
      viewId = firstView.id
    }

    // If a view id is provided and the table is selected we can select the view. The
    // views that belong to the table have already been fetched so we just need to
    // select the correct one.
    if (viewId !== null) {
      try {
        const { view } = await store.dispatch('view/selectById', viewId)
        data.view = view

        // It might be possible that the view also has some stores that need to be
        // filled with initial data so we're going to call the fetch function here.
        const type = app.$registry.get('view', view.type)
        await type.fetch({ store }, view, data.fields, data.primary, 'page/')
      } catch (e) {
        // In case of a network error we want to fail hard.
        if (e.response === undefined && !(e instanceof StoreItemLookupError)) {
          throw e
        }

        return error({ statusCode: 404, message: 'View not found.' })
      }
    }

    return data
  },
  head() {
    return {
      title: (this.view ? this.view.name + ' - ' : '') + this.table.name,
    }
  },
  computed: {
    ...mapState({
      // We need the tableLoading state to show a small loading animation when
      // switching between views. Because some of the data will be populated by
      // the asyncData function and some by mapping the state of a store it could look
      // a bit strange for the user when switching between views because not all data
      // renders at the same time. That is why we show this loading animation. Store
      // changes are always rendered right away.
      tableLoading: (state) => state.table.loading,
      views: (state) => state.view.items,
    }),
  },
  /**
   * The beforeCreate hook is called right after the asyncData finishes and when the
   * page has been rendered for the first time. The perfect moment to stop the table
   * loading animation.
   */
  beforeCreate() {
    this.$store.dispatch('table/setLoading', false)
  },
  mounted() {
    this.$realtime.subscribe('table', { table_id: this.table.id })
  },
  beforeDestroy() {
    this.$realtime.subscribe(null)
  },
  methods: {
    selectedView(view) {
      this.$nuxt.$router.push({
        name: 'database-table',
        params: {
          viewId: view.id,
        },
      })
    },
  },
}
</script>
