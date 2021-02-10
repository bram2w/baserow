<template>
  <div>
    <header class="layout__col-2-1 header">
      <div v-show="tableLoading" class="header__loading"></div>
      <ul v-if="!tableLoading" class="header__filter">
        <li class="header__filter-item header__filter-item--grids">
          <a
            ref="viewsSelectToggle"
            class="header__filter-link"
            @click="
              $refs.viewsContext.toggle(
                $refs.viewsSelectToggle,
                'bottom',
                'left',
                4
              )
            "
          >
            <span v-if="hasSelectedView">
              <i
                class="header__filter-icon header-filter-icon--view fas"
                :class="'fa-' + view._.type.iconClass"
              ></i>
              {{ view.name }}
            </span>
            <span v-else>
              <i
                class="header__filter-icon header-filter-icon-no-choice fas fa-caret-square-down"
              ></i>
              Choose view
            </span>
          </a>
          <ViewsContext ref="viewsContext" :table="table"></ViewsContext>
        </li>
        <li
          v-if="hasSelectedView && view._.type.canFilter"
          class="header__filter-item"
        >
          <ViewFilter
            :view="view"
            :fields="fields"
            :primary="primary"
            @changed="refresh()"
          ></ViewFilter>
        </li>
        <li
          v-if="hasSelectedView && view._.type.canSort"
          class="header__filter-item"
        >
          <ViewSort
            :view="view"
            :fields="fields"
            :primary="primary"
            @changed="refresh()"
          ></ViewSort>
        </li>
      </ul>
      <component
        :is="getViewHeaderComponent(view)"
        v-if="hasSelectedView"
        :database="database"
        :table="table"
        :view="view"
        :fields="fields"
        :primary="primary"
      />
      <ul v-if="!tableLoading" class="header__info">
        <li>{{ database.name }}</li>
        <li>{{ table.name }}</li>
      </ul>
    </header>
    <div class="layout__col-2-2 content">
      <component
        :is="getViewComponent(view)"
        v-if="hasSelectedView && !tableLoading"
        ref="view"
        :database="database"
        :table="table"
        :view="view"
        :fields="fields"
        :primary="primary"
        @refresh="refresh"
      />
      <div v-if="viewLoading" class="loading-overlay"></div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

import ViewsContext from '@baserow/modules/database/components/view/ViewsContext'
import ViewFilter from '@baserow/modules/database/components/view/ViewFilter'
import ViewSort from '@baserow/modules/database/components/view/ViewSort'

/**
 * This page component is the skeleton for a table. Depending on the selected view it
 * will load the correct components into the header and body.
 */
export default {
  components: {
    ViewsContext,
    ViewFilter,
    ViewSort,
  },
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
      if (e.response === undefined) {
        throw e
      }

      return error({ statusCode: 404, message: 'Table not found.' })
    }

    // After selecting the table the fields become available which need to be added to
    // the data.
    data.fields = store.getters['field/getAll']
    data.primary = store.getters['field/getPrimary']

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
        await type.fetch({ store }, view)
      } catch (e) {
        // In case of a network error we want to fail hard.
        if (e.response === undefined) {
          throw e
        }

        return error({ statusCode: 404, message: 'View not found.' })
      }
    }

    return data
  },
  data() {
    return {
      // Shows a small spinning loading animation when the view is being refreshed.
      viewLoading: false,
    }
  },
  head() {
    return {
      title: (this.view ? this.view.name + ' - ' : '') + this.table.name,
    }
  },
  computed: {
    /**
     * Indicates if there is a selected view by checking if the view object has been
     * populated.
     */
    hasSelectedView() {
      return (
        this.view !== undefined &&
        Object.prototype.hasOwnProperty.call(this.view, '_')
      )
    },
    ...mapState({
      // We need the tableLoading state to show a small loading animation when
      // switching between views. Because some of the data will be populated by
      // the asyncData function and some by mapping the state of a store it could look
      // a bit strange for the user when switching between views because not all data
      // renders at the same time. That is why we show this loading animation. Store
      // changes are always rendered right away.
      tableLoading: (state) => state.table.loading,
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
  beforeMount() {
    this.$bus.$on('table-refresh', this.refresh)
  },
  mounted() {
    this.$realtime.subscribe('table', { table_id: this.table.id })
  },
  beforeDestroy() {
    this.$bus.$off('table-refresh', this.refresh)
    this.$realtime.subscribe(null)
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
    /**
     * Refreshes the whole view. All data will be reloaded and it will visually look
     * the same as seeing the view for the first time.
     */
    async refresh(event) {
      this.viewLoading = true
      const type = this.$registry.get('view', this.view.type)
      await type.refresh({ store: this.$store }, this.view)
      if (
        Object.prototype.hasOwnProperty.call(this.$refs, 'view') &&
        Object.prototype.hasOwnProperty.call(this.$refs.view, 'refresh')
      ) {
        await this.$refs.view.refresh()
      }
      // It might be possible that the event has a callback that needs to be called
      // after the rows are refreshed. This is for example the case when a field has
      // changed. In that case we want to update the field in the store after the rows
      // have been refreshed to prevent incompatible values in field types.
      if (event && Object.prototype.hasOwnProperty.call(event, 'callback')) {
        await event.callback()
      }
      this.$nextTick(() => {
        this.viewLoading = false
      })
    },
  },
}
</script>
