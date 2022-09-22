<template>
  <div>
    <Table
      :database="database"
      :table="table"
      :fields="fields"
      :views="views"
      :view="view"
      :table-loading="tableLoading"
      store-prefix="page/"
      @selected-view="selectedView"
      @selected-row="selectRow"
      @navigate-previous="
        (row, activeSearchTerm) => setAdjacentRow(true, row, activeSearchTerm)
      "
      @navigate-next="
        (row, activeSearchTerm) => setAdjacentRow(false, row, activeSearchTerm)
      "
    ></Table>
  </div>
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
    this.$store.dispatch('view/unselect')
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
    data.view = undefined

    // Because we do not have a dashboard for the table yet we're going to redirect to
    // the first available view.
    const firstView = store.getters['view/first']
    if (viewId === null && firstView !== null) {
      const firstViewType = app.$registry.get('view', firstView.type)
      // If the view is deactivated, it's not possible to open the view because it will
      // put the user in an unrecoverable state. Therefore, it's better to not select a
      // view, so that the user can choose which he wants to select in the top left
      // corner.
      if (!firstViewType.isDeactivated(data.database.group.id)) {
        viewId = firstView.id
      }
    }

    // If a view id is provided and the table is selected we can select the view. The
    // views that belong to the table have already been fetched so we just need to
    // select the correct one.
    if (viewId !== null && viewId !== 0) {
      try {
        const { view } = await store.dispatch('view/selectById', viewId)
        data.view = view

        // It might be possible that the view also has some stores that need to be
        // filled with initial data so we're going to call the fetch function here.
        const type = app.$registry.get('view', view.type)

        if (type.isDeactivated(data.database.group.id)) {
          return error({ statusCode: 400, message: type.getDeactivatedText() })
        }

        await type.fetch({ store }, view, data.fields, 'page/')
      } catch (e) {
        // In case of a network error we want to fail hard.
        if (e.response === undefined && !(e instanceof StoreItemLookupError)) {
          throw e
        }

        return error({ statusCode: 404, message: 'View not found.' })
      }
    }

    if (params.rowId) {
      try {
        await store.dispatch('rowModalNavigation/fetchRow', {
          tableId,
          rowId: params.rowId,
        })
      } catch (e) {
        return error({ statusCode: 404, message: 'Row not found.' })
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
      if (this.view && this.view.id === view.id) {
        return
      }

      this.$nuxt.$router.push({
        name: 'database-table',
        params: {
          viewId: view.id,
        },
      })
    },
    async setAdjacentRow(previous, row = null, activeSearchTerm = null) {
      if (row) {
        await this.$store.dispatch('rowModalNavigation/setRow', row)
        this.updatePath(row.id)
      } else {
        // If the row isn't provided then the row is
        // probably not visible to the user at the moment
        // and needs to be fetched
        await this.fetchAdjacentRow(previous, activeSearchTerm)
      }
    },
    async selectRow(rowId) {
      if (rowId) {
        const row = await this.$store.dispatch('rowModalNavigation/fetchRow', {
          tableId: this.table.id,
          rowId,
        })
        if (row) {
          this.updatePath(rowId)
        }
      } else {
        await this.$store.dispatch('rowModalNavigation/clearRow')
        this.updatePath(rowId)
      }
    },
    updatePath(rowId) {
      if (
        this.$route.params.rowId !== undefined &&
        this.$route.params.rowId === rowId
      ) {
        return
      }

      const newPath = this.$nuxt.$router.resolve({
        name: rowId ? 'database-table-row' : 'database-table',
        params: {
          databaseId: this.database.id,
          tableId: this.table.id,
          viewId: this.view?.id,
          rowId,
        },
      }).href
      history.replaceState({}, null, newPath)
    },
    async fetchAdjacentRow(previous, activeSearchTerm = null) {
      const { row, status } = await this.$store.dispatch(
        'rowModalNavigation/fetchAdjacentRow',
        {
          tableId: this.table.id,
          viewId: this.view?.id,
          activeSearchTerm,
          previous,
        }
      )

      if (status === 204 || status === 404) {
        const translationPath = `table.adjacentRow.notification.notFound.${
          previous ? 'previous' : 'next'
        }`
        await this.$store.dispatch('notification/info', {
          title: this.$t(`${translationPath}.title`),
          message: this.$t(`${translationPath}.message`),
        })
      } else if (status !== 200) {
        await this.$store.dispatch('notification/error', {
          title: this.$t(`table.adjacentRow.notification.error.title`),
          message: this.$t(`table.adjacentRow.notification.error.message`),
        })
      }

      if (row) {
        this.updatePath(row.id)
      }
    },
  },
}
</script>
