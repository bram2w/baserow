<template>
  <div class="crudtable">
    <header class="crudtable__header">
      <slot name="header"></slot>
      <CrudTableSearch :loading="loading" @search-changed="doSearch" />
    </header>
    <div
      :class="{ crudtable__loading: loading }"
      class="crudtable__rows"
      :style="{
        'grid-template-columns': columnWidths,
      }"
    >
      <template v-for="col in allColumns">
        <div
          :key="col.key"
          class="crudtable__field"
          :class="{
            'crudtable__field--sticky': col.isInLeftSection,
            'crudtable__field--right': col.hasRightBar,
            'crudtable__field--sortable': col.sortable,
          }"
          @click="toggleSort(col)"
        >
          <span class="crudtable__field-header-title">
            {{ col.header }}
          </span>
          <template v-if="sorted(col)">
            <i class="crudtable__field-icon fas" :class="sortIcon(col)"></i>
            <span class="crudtable__sortindex"> {{ sortIndex(col) }} </span>
          </template>
        </div>
      </template>
      <template v-for="row in rows">
        <template v-for="(col, index) in allColumns">
          <component
            :is="col.cellComponent"
            :key="col.key + '-' + row.id"
            :row="row"
            :column="col"
            class="crudtable__cell"
            :class="{
              'crudtable__cell--sticky': col.isInLeftSection,
              'crudtable__cell--right': col.hasRightBar,
              'crudtable__cell--last':
                index === Object.keys(allColumns).length - 1,
            }"
            @contextmenu.prevent="
              $emit('row-context', { col, row, event: $event })
            "
            v-on="$listeners"
            @row-update="updateRow"
            @row-delete="deleteRow"
          />
        </template>
      </template>
    </div>
    <div class="crudtable__footer">
      <Paginator
        :page="page"
        :total-pages="totalPages"
        @change-page="fetchPage"
      ></Paginator>
    </div>
    <slot name="menus" :updateRow="updateRow" :deleteRow="deleteRow"></slot>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import CrudTableSearch from '@baserow_premium/components/crud_table/CrudTableSearch'
import Paginator from '@baserow/modules/core/components/Paginator'
import CrudTableColumn from '@baserow_premium/crud_table/crudTableColumn'

/**
 * This component is a generic wrapper for a basic crud service which displays its
 * data in a table format. Comes with basic features like column sorting, searching
 * by a field etc.
 *
 * Any listeners placed on the CrudTable will be passed through and placed on every
 * instance of the provided columns cellComponent. This allows components using
 * CrudTable to easily communicate with their specific cellComponents.
 *
 * Provides two slots:
 *  #header: Placed within the header of the CrudTable.
 *  #menus: Placed in the footer and expected to only contain Contexts and Modals.
 *          Two slot props are provided `updateRow` and `deleteRow` which are functions
 *          called when your menu has changed the row state which trigger the CrudTable
 *          to rerender the rows with the new data.
 */
export default {
  name: 'CrudTable',
  components: { Paginator, CrudTableSearch },
  props: {
    /**
     * A service which provides a fetchPage(pageNumber, searchParam, columnSortsList)
     * method which returns an object in the form of:
     * ```
     * {
     *   count: 1, // the number of total results available (including other pages)
     *   results: [ // A row object with an attribute matching the provided column keys
     *     {
     *       column1Key: value,
     *       column2Key: value
     *     }
     *   ]
     * }
     * ```
     * CrudTable will call this method with the current page and assume the returned
     * results have a max page size of 100 to calculate the total number of pages.
     *
     * If the user has provided a search query this will be passed in the second
     * argument.
     *
     * Finally if the user has sorted sortable columns they will be passed in the third
     * argument as an ordered array of objects in the form of:
     * ```
     * {
     *   key: 'column1Key',
     *   direction: 'asc' or 'desc',
     * }
     * ```
     */
    service: {
      required: true,
      type: Object,
    },
    /**
     * An ordered array of columns to show in the sticky left section of columns,
     * there will be a visual separator between the left and right column sections.
     * The column keys must be present in every row returned by the service.
     */
    leftColumns: {
      required: false,
      type: Array,
      default: () => [],
      validator: (prop) => prop.every((e) => e instanceof CrudTableColumn),
    },
    /**
     * An ordered array of columns to show in the right section of columns.
     */
    rightColumns: {
      required: true,
      type: Array,
      validator: (prop) => prop.every((e) => e instanceof CrudTableColumn),
    },
    /**
     * The row attribute to be used as the key for the row. Must be present on every row
     * returned from the service.
     * The delete-row cellComponent event / deleteRow slot prop expects that the
     * emitted/passed object is the rowIdKey value for the row to be deleted.
     * The edit-row cellComponent event / editRow slotProp expects the row object
     * emitted/passed contains this key.
     */
    rowIdKey: {
      required: true,
      type: String,
    },
  },
  data() {
    return {
      loading: false,
      page: 1,
      totalPages: null,
      searchQuery: false,
      rows: [],
      columnSorts: [],
    }
  },
  async fetch() {
    await this.fetchPage(1, {})
  },
  computed: {
    allColumns() {
      this.leftColumns.forEach((c, i) => {
        c.isInLeftSection = true
        if (i === this.leftColumns.length - 1) {
          c.hasRightBar = true
        }
      })
      return this.leftColumns.concat(this.rightColumns)
    },
    columnWidths() {
      return this.allColumns
        .map((c) => `minmax(${c.minWidth}, ${c.maxWidth})`)
        .join(' ')
    },
  },
  methods: {
    /**
     * If the column is sortable cycles through applying descending, then ascending and
     * then no sort to this column.
     */
    toggleSort(column) {
      if (!column.sortable) {
        return
      }
      const i = this.sortIndex(column)
      if (i === -1) {
        this.columnSorts.push({ key: column.key, direction: 'desc' })
      } else {
        const current = this.columnSorts[i]
        if (current.direction === 'desc') {
          this.columnSorts.splice(i, 1, {
            key: current.key,
            direction: 'asc',
          })
        } else {
          this.columnSorts.splice(i, 1)
        }
      }
      this.fetchPage(1)
    },
    sortIcon(column) {
      const i = this.sortIndex(column)
      return this.columnSorts[i].direction === 'desc'
        ? 'fa-sort-down'
        : 'fa-sort-up'
    },
    sorted(column) {
      return this.sortIndex(column) !== -1
    },
    sortIndex(column) {
      return this.columnSorts.findIndex((c) => c.key === column.key)
    },
    async doSearch(searchQuery) {
      this.totalPages = null
      this.searchQuery = searchQuery
      await this.fetchPage(1)
    },
    /**
     * Fetches the rows of a given page and adds them to the state.
     */
    async fetchPage(page) {
      this.loading = true

      try {
        const { data } = await this.service.fetchPage(
          page,
          this.searchQuery,
          this.columnSorts
        )
        this.page = page
        this.totalPages = Math.ceil(data.count / 100)
        this.rows = data.results
      } catch (error) {
        notifyIf(error, 'row')
      }

      this.loading = false
    },
    updateRow(updatedRow) {
      const i = this.rows.findIndex(
        (u) => u[this.rowIdKey] === updatedRow[this.rowIdKey]
      )
      this.rows.splice(i, 1, updatedRow)
    },
    deleteRow(rowId) {
      const i = this.rows.findIndex((u) => u[this.rowIdKey] === rowId)
      this.rows.splice(i, 1)
    },
  },
}
</script>
