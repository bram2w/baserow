<template>
  <div>
    <header
      ref="header"
      class="layout__col-2-1 header"
      :class="{ 'header--overflow': headerOverflow }"
    >
      <div v-show="tableLoading" class="header__loading"></div>
      <ul v-if="!tableLoading" class="header__filter">
        <li v-if="showLogo" class="header__filter-item">
          <BaserowLogo class="header__filter-logo" />
        </li>
        <li class="header__filter-item header__filter-item--grids">
          <a
            ref="viewsSelectToggle"
            class="header__filter-link"
            :class="{ 'header__filter-link--disabled': views === null }"
            @click="
              views !== null &&
                $refs.viewsContext.toggle(
                  $refs.viewsSelectToggle,
                  'bottom',
                  'left',
                  4
                )
            "
          >
            <template v-if="hasSelectedView">
              <i
                class="header__filter-icon header-filter-icon--view fas fa-fw"
                :class="view._.type.colorClass + ' fa-' + view._.type.iconClass"
              ></i>
              <span class="header__filter-name header__filter-name--forced">
                <EditableViewName ref="rename" :view="view"></EditableViewName>
              </span>
            </template>
            <span v-else-if="view !== null">
              <i class="header__filter-icon fas fa-caret-square-down"></i>
              {{ $t('table.chooseView') }}
            </span>
          </a>
          <ViewsContext
            v-if="views !== null"
            ref="viewsContext"
            :database="database"
            :table="table"
            :views="views"
            :read-only="readOnly"
            :header-overflow="headerOverflow"
            @selected-view="$emit('selected-view', $event)"
          ></ViewsContext>
        </li>
        <li
          v-if="hasSelectedView && !readOnly && showViewContext"
          class="header__filter-item header__filter-item--no-margin-left"
        >
          <a
            class="header__filter-link"
            @click="
              $refs.viewContext.toggle(
                $event.currentTarget,
                'bottom',
                'left',
                4
              )
            "
          >
            <i class="header__filter-icon fas fa-ellipsis-h"></i>
          </a>
          <ViewContext
            ref="viewContext"
            :database="database"
            :view="view"
            :table="table"
            @enable-rename="$refs.rename.edit()"
          >
          </ViewContext>
        </li>
        <li
          v-if="
            hasSelectedView &&
            view._.type.canFilter &&
            (readOnly ||
              $hasPermission(
                'database.table.view.create_filter',
                view,
                database.group.id
              ))
          "
          class="header__filter-item"
        >
          <ViewFilter
            :view="view"
            :fields="fields"
            :read-only="readOnly"
            :disable-filter="disableFilter"
            @changed="refresh()"
          ></ViewFilter>
        </li>
        <li
          v-if="
            hasSelectedView &&
            view._.type.canSort &&
            (readOnly ||
              $hasPermission(
                'database.table.view.create_sort',
                view,
                database.group.id
              ))
          "
          class="header__filter-item"
        >
          <ViewSort
            :view="view"
            :fields="fields"
            :read-only="readOnly"
            :disable-sort="disableSort"
            @changed="refresh()"
          ></ViewSort>
        </li>
        <li
          v-if="
            hasSelectedView &&
            view._.type.canShare &&
            !readOnly &&
            $hasPermission(
              'database.table.view.update_slug',
              view,
              database.group.id
            )
          "
          class="header__filter-item"
        >
          <ShareViewLink :view="view" :read-only="readOnly"></ShareViewLink>
        </li>
        <li
          v-if="
            hasCompatibleDecorator &&
            !readOnly &&
            $hasPermission(
              'database.table.view.decoration.update',
              view,
              database.group.id
            )
          "
          class="header__filter-item"
        >
          <ViewDecoratorMenu
            :database="database"
            :view="view"
            :table="table"
            :fields="fields"
            :read-only="readOnly"
            :disable-sort="disableSort"
            @changed="refresh()"
          ></ViewDecoratorMenu>
        </li>
      </ul>
      <component
        :is="getViewHeaderComponent(view)"
        v-if="!tableLoading && hasSelectedView"
        :database="database"
        :table="table"
        :view="view"
        :fields="fields"
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
        :read-only="readOnly"
        :store-prefix="storePrefix"
        @refresh="refresh"
        @selected-row="$emit('selected-row', $event)"
        @navigate-previous="
          (row, activeSearchTerm) =>
            $emit('navigate-previous', row, activeSearchTerm)
        "
        @navigate-next="
          (row, activeSearchTerm) =>
            $emit('navigate-next', row, activeSearchTerm)
        "
      />
      <div v-if="viewLoading" class="loading-overlay"></div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import ResizeObserver from 'resize-observer-polyfill'

import { RefreshCancelledError } from '@baserow/modules/core/errors'
import { notifyIf } from '@baserow/modules/core/utils/error'
import ViewsContext from '@baserow/modules/database/components/view/ViewsContext'
import ViewContext from '@baserow/modules/database/components/view/ViewContext'
import ViewFilter from '@baserow/modules/database/components/view/ViewFilter'
import ViewSort from '@baserow/modules/database/components/view/ViewSort'
import ViewDecoratorMenu from '@baserow/modules/database/components/view/ViewDecoratorMenu'
import ViewSearch from '@baserow/modules/database/components/view/ViewSearch'
import EditableViewName from '@baserow/modules/database/components/view/EditableViewName'
import ShareViewLink from '@baserow/modules/database/components/view/ShareViewLink'
import BaserowLogo from '@baserow/modules/core/components/BaserowLogo'

/**
 * This page component is the skeleton for a table. Depending on the selected view it
 * will load the correct components into the header and body.
 */
export default {
  components: {
    BaserowLogo,
    ShareViewLink,
    EditableViewName,
    ViewsContext,
    ViewDecoratorMenu,
    ViewFilter,
    ViewSort,
    ViewSearch,
    ViewContext,
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
    views: {
      required: false,
      validator: (prop) => typeof prop === 'object' || prop === undefined,
      default: null,
    },
    view: {
      required: true,
      validator: (prop) => typeof prop === 'object' || prop === undefined,
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
    disableFilter: {
      type: Boolean,
      required: false,
      default: false,
    },
    disableSort: {
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
      // Indicates if the elements within the header are overflowing. In case of true,
      // we can hide certain values to make sure that it fits within the header.
      headerOverflow: false,
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
    hasCompatibleDecorator() {
      return (
        this.view !== undefined &&
        this.$registry
          .getOrderedList('viewDecorator')
          .some((deco) => deco.isCompatible(this.view))
      )
    },
    showLogo() {
      return this.view?.show_logo && this.isPublic
    },
    showViewContext() {
      return (
        this.$hasPermission(
          'database.table.run_export',
          this.table,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.import_rows',
          this.table,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.view.duplicate',
          this.table,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.view.update',
          this.table,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.view.delete',
          this.table,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.create_webhook',
          this.table,
          this.database.group.id
        )
      )
    },
    ...mapGetters({
      isPublic: 'page/view/public/getIsPublic',
    }),
  },
  watch: {
    tableLoading(value) {
      if (!value) {
        this.$nextTick(() => {
          this.checkHeaderOverflow()
        })
      }
    },
  },
  beforeMount() {
    this.$bus.$on('table-refresh', this.refresh)
  },
  mounted() {
    this.$el.resizeObserver = new ResizeObserver(this.checkHeaderOverflow)
    this.$el.resizeObserver.observe(this.$el)
  },
  beforeDestroy() {
    this.$bus.$off('table-refresh', this.refresh)
    this.$el.resizeObserver.unobserve(this.$el)
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
     * When the window resizes, we want to check if the content of the header is
     * overflowing. If that is the case, we want to make some space by removing some
     * content. We do this by copying the header content into a new HTMLElement and
     * check if the elements still fit within the header. We copy the html because we
     * want to measure the header in the full width state.
     */
    checkHeaderOverflow() {
      const header = this.$refs.header
      const width = header.getBoundingClientRect().width
      const wrapper = document.createElement('div')
      wrapper.innerHTML = header.outerHTML
      const el = wrapper.childNodes[0]
      el.style = `position: absolute; left: 0; top: 0; width: ${width}px; overflow: auto;`
      el.classList.remove('header--overflow')
      document.body.appendChild(el)
      this.headerOverflow =
        el.clientWidth < el.scrollWidth || el.clientHeight < el.scrollHeight
      document.body.removeChild(el)
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

      const includeFieldOptions =
        typeof event === 'object' ? event.includeFieldOptions : false

      const fieldsToRefresh =
        typeof event === 'object' && event.newField
          ? [...this.fields, event.newField]
          : this.fields

      this.viewLoading = true
      const type = this.$registry.get('view', this.view.type)
      try {
        await type.refresh(
          { store: this.$store },
          this.view,
          fieldsToRefresh,
          this.storePrefix,
          includeFieldOptions
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
