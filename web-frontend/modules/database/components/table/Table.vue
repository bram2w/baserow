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
          <ViewsContext
            ref="viewsContext"
            :table="table"
            :views="views"
            :read-only="readOnly"
            @selected-view="$emit('selected-view', $event)"
          ></ViewsContext>
        </li>
        <li
          v-if="hasSelectedView && view._.type.canFilter"
          class="header__filter-item"
        >
          <ViewFilter
            :view="view"
            :fields="fields"
            :primary="primary"
            :read-only="readOnly"
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
            :read-only="readOnly"
            @changed="refresh()"
          ></ViewSort>
        </li>
      </ul>
      <component
        :is="getViewHeaderComponent(view)"
        v-if="!tableLoading && hasSelectedView"
        :database="database"
        :table="table"
        :view="view"
        :fields="fields"
        :primary="primary"
        :read-only="readOnly"
        :store-prefix="storePrefix"
        @refresh="refresh"
      />
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
        :read-only="readOnly"
        :store-prefix="storePrefix"
        @refresh="refresh"
      />
      <div v-if="viewLoading" class="loading-overlay"></div>
    </div>
  </div>
</template>

<script>
import { RefreshCancelledError } from '@baserow/modules/core/errors'
import { notifyIf } from '@baserow/modules/core/utils/error'
import ViewsContext from '@baserow/modules/database/components/view/ViewsContext'
import ViewFilter from '@baserow/modules/database/components/view/ViewFilter'
import ViewSort from '@baserow/modules/database/components/view/ViewSort'
import ViewSearch from '@baserow/modules/database/components/view/ViewSearch'

/**
 * This page component is the skeleton for a table. Depending on the selected view it
 * will load the correct components into the header and body.
 */
export default {
  components: {
    ViewsContext,
    ViewFilter,
    ViewSort,
    ViewSearch,
  },
  /**
   * Because there is no hook that is called before the route changes, we need the
   * tableLoading middleware to change the table loading state. This change will get
   * rendered right away. This allows us to have a custom loading animation when
   * switching views.
   */
  middleware: ['tableLoading'],
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    primary: {
      type: Object,
      required: true,
    },
    views: {
      type: Array,
      required: true,
    },
    view: {
      validator: (prop) => typeof prop === 'object' || prop === undefined,
      required: true,
    },
    tableLoading: {
      type: Boolean,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: false,
      default: false,
    },
    storePrefix: {
      type: String,
      required: false,
      default: '',
    },
  },
  data() {
    return {
      // Shows a small spinning loading animation when the view is being refreshed.
      viewLoading: false,
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
  },
  beforeMount() {
    this.$bus.$on('table-refresh', this.refresh)
  },
  beforeDestroy() {
    this.$bus.$off('table-refresh', this.refresh)
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
      // If could be that the refresh event is for a specific table and in table case
      // we check if the refresh event is related to this table and stop if that is not
      // the case.
      if (
        typeof event === 'object' &&
        Object.prototype.hasOwnProperty.call(event, 'tableId') &&
        event.tableId !== this.table.id
      ) {
        return
      }

      this.viewLoading = true
      const type = this.$registry.get('view', this.view.type)
      try {
        await type.refresh(
          { store: this.$store },
          this.view,
          this.fields,
          this.primary,
          this.storePrefix
        )
      } catch (error) {
        if (error instanceof RefreshCancelledError) {
          // Multiple refresh calls have been made and the view has indicated that
          // this particular one should be cancelled. However we do not want to
          // set viewLoading back to false as the other non cancelled call/s might
          // still be loading.
          return
        } else {
          notifyIf(error)
        }
      }
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
