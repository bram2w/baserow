<template>
  <div>
    <header class="layout__col-3-1 header">
      <ul class="header__filter">
        <li class="header__filter-item">
          <a
            ref="viewsSelectToggle"
            class="header__filter-link"
            @click="$refs.viewsContext.toggle($refs.viewsSelectToggle)"
          >
            <span v-if="hasSelectedView">
              <i
                class="header__filter-icon fas"
                :class="'fa-' + selectedView._.type.iconClass"
              ></i>
              {{ selectedView.name }}
            </span>
            <span v-if="!hasSelectedView">
              <i
                class="header__filter-icon header-filter-icon-no-choice fas fa-caret-square-down"
              ></i>
              Choose view
            </span>
          </a>
          <ViewsContext ref="viewsContext" :table="table"></ViewsContext>
        </li>
      </ul>
      <template v-if="hasSelectedView">
        <component
          :is="getViewHeaderComponent(selectedView)"
          :database="database"
          :table="table"
          :view="selectedView"
          :fields="fields"
          :primary="primary"
        />
      </template>
      <ul class="header__info">
        <li>{{ database.name }}</li>
        <li>{{ table.name }}</li>
      </ul>
    </header>
    <div class="layout__col-3-2 content">
      <template v-if="hasSelectedView">
        <component
          :is="getViewComponent(selectedView)"
          :database="database"
          :table="table"
          :view="selectedView"
          :fields="fields"
          :primary="primary"
        />
      </template>
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters } from 'vuex'

import ViewsContext from '@baserow/modules/database/components/view/ViewsContext'

/**
 * This page component is the skeleton for a table. Depending on the selected view it
 * will load the correct components into the header and body.
 */
export default {
  layout: 'app',
  components: {
    ViewsContext,
  },
  /**
   * Prepares all the table, field and view data for the provided database, table and
   * view id.
   */
  async asyncData({ store, params, error, redirect, app }) {
    // @TODO figure out why the id's aren't converted to an int in the route.
    const databaseId = parseInt(params.databaseId)
    const tableId = parseInt(params.tableId)
    const viewId = params.viewId ? parseInt(params.viewId) : null
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
      return error({ statusCode: 404, message: 'Table not found.' })
    }

    // Because we do not have a dashboard for the table yet we're going to redirect to
    // the first available view.
    if (viewId === null) {
      const firstView = store.getters['view/first']
      if (firstView !== null) {
        return redirect({
          name: 'database-table',
          params: {
            databaseId: data.database.id,
            tableId: data.table.id,
            viewId: firstView.id,
          },
        })
      }
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
        await type.fetch({ store }, view)
      } catch {
        return error({ statusCode: 404, message: 'View not found.' })
      }
    }

    return data
  },
  computed: {
    ...mapState({
      selectedView: (state) => state.view.selected,
      fields: (state) => state.field.items,
      primary: (state) => state.field.primary,
    }),
    ...mapGetters({
      hasSelectedView: 'view/hasSelected',
    }),
  },
  beforeRouteLeave(to, from, next) {
    this.$store.dispatch('table/unselect')
    next()
  },
  methods: {
    getViewComponent(view) {
      const type = this.$registry.get('view', view.type)
      return type.getComponent()
    },
    getViewHeaderComponent(view) {
      const type = this.$registry.get('view', view.type)
      return type.getHeaderComponent()
    },
  },
  head() {
    return {
      title: (this.view ? this.view.name + ' - ' : '') + this.table.name,
    }
  },
}
</script>
