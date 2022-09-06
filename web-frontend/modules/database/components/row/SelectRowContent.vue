<template>
  <div>
    <div v-if="!loaded" class="select-row-modal__initial-loading"></div>
    <div v-if="loaded" :class="{ 'select-row-modal__loading': loading }">
      <Scrollbars
        ref="scrollbars"
        horizontal="getHorizontalScrollbarElement"
        :style="{ left: '240px' }"
        @horizontal="horizontalScroll"
      ></Scrollbars>
      <div class="select-row-modal__search">
        <i class="fas fa-search select-row-modal__search-icon"></i>
        <input
          ref="search"
          v-model="visibleSearch"
          type="text"
          :placeholder="$t('selectRowContent.search')"
          class="input select-row-modal__search-input"
          @input="doSearch(visibleSearch, false)"
          @keypress.enter="doSearch(visibleSearch, true)"
        />
      </div>
      <div v-scroll="scroll" class="select-row-modal__rows">
        <div class="select-row-modal__left">
          <div class="select-row-modal__head">
            <div
              class="select-row-modal__field select-row-modal__field--first"
            ></div>
            <div class="select-row-modal__field">
              <i
                class="fas select-row-modal__field-icon"
                :class="'fa-' + primary._.type.iconClass"
              ></i>
              {{ primary.name }}
            </div>
          </div>
          <div class="select-row-modal__body">
            <div
              v-for="row in rows"
              :key="'left-select-row-' + tableId + '-' + row.id"
              class="select-row-modal__row"
              :class="{
                'select-row-modal__row--hover': row._.hover,
                'select-row-modal__row--selected': isAlreadySelected(row.id),
              }"
              @mouseover="setRowHover(row, true)"
              @mouseleave="setRowHover(row, false)"
              @click="select(row, primary, fields)"
            >
              <div class="select-row-modal__cell select-row-modal__cell--first">
                {{ row.id }}
              </div>
              <div class="select-row-modal__cell">
                <SelectRowField :field="primary" :row="row"></SelectRowField>
              </div>
            </div>
            <div
              class="select-row-modal__row"
              :class="{ 'select-row-modal__row--hover': addRowHover }"
              @mouseover="addRowHover = true"
              @mouseleave="addRowHover = false"
              @click="$refs.rowCreateModal.show()"
            >
              <a
                class="
                  select-row-modal__cell
                  select-row-modal__cell--single
                  select-row-modal__add-row
                "
                ><i class="fas fa-plus"></i
              ></a>
            </div>
          </div>
          <div class="select-row-modal__foot">
            <Paginator
              :total-pages="totalPages"
              :page="page"
              @change-page="fetch"
            ></Paginator>
          </div>
        </div>
        <div ref="right" class="select-row-modal__right">
          <div class="select-row-modal__head">
            <div
              v-for="field in fields"
              :key="field.id"
              class="select-row-modal__field"
            >
              <i
                class="fas select-row-modal__field-icon"
                :class="'fa-' + field._.type.iconClass"
              ></i>
              {{ field.name }}
            </div>
          </div>
          <div class="select-row-modal__body">
            <div
              v-for="row in rows"
              :key="'right-select-row-' + tableId + '-' + row.id"
              class="select-row-modal__row"
              :class="{
                'select-row-modal__row--hover': row._.hover,
                'select-row-modal__row--selected': isAlreadySelected(row.id),
              }"
              @mouseover="setRowHover(row, true)"
              @mouseleave="setRowHover(row, false)"
              @click="select(row, primary, fields)"
            >
              <div
                v-for="field in fields"
                :key="'select-row-' + row.id + '-field-' + field.id"
                class="select-row-modal__cell"
              >
                <SelectRowField :field="field" :row="row"></SelectRowField>
              </div>
            </div>
            <div
              class="select-row-modal__row"
              :style="{ width: addRowWidth }"
              :class="{ 'select-row-modal__row--hover': addRowHover }"
              @mouseover="addRowHover = true"
              @mouseleave="addRowHover = false"
              @click="$refs.rowCreateModal.show()"
            >
              <div
                class="select-row-modal__cell select-row-modal__cell--single"
              ></div>
            </div>
          </div>
          <div
            class="select-row-modal__foot"
            :style="{
              width: fields.length * 200 + 'px',
            }"
          ></div>
        </div>
      </div>
    </div>
    <RowCreateModal
      v-if="table"
      ref="rowCreateModal"
      :table="table"
      :sortable="false"
      :visible-fields="allFields"
      :can-modify-fields="false"
      @created="createRow"
    ></RowCreateModal>
  </div>
</template>

<script>
import debounce from 'lodash/debounce'

import { notifyIf } from '@baserow/modules/core/utils/error'
import FieldService from '@baserow/modules/database/services/field'
import { populateField } from '@baserow/modules/database/store/field'
import RowService from '@baserow/modules/database/services/row'
import { populateRow } from '@baserow/modules/database/store/view/grid'
import ViewService from '@baserow/modules/database/services/view'

import Paginator from '@baserow/modules/core/components/Paginator'
import SelectRowField from '@baserow/modules/database/components/row/SelectRowField'
import RowCreateModal from '@baserow/modules/database/components/row/RowCreateModal'
import { prepareRowForRequest } from '@baserow/modules/database/utils/row'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import {
  filterVisibleFieldsFunction,
  sortFieldsByOrderAndIdFunction,
} from '@baserow/modules/database/utils/view'
import { GridViewType } from '@baserow/modules/database/viewTypes'

export default {
  name: 'SelectRowContent',
  components: { Paginator, SelectRowField, RowCreateModal },
  props: {
    tableId: {
      type: Number,
      required: true,
    },
    value: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  data() {
    return {
      loading: false,
      loaded: false,
      primary: null,
      fields: null,
      rows: [],
      search: '',
      visibleSearch: '',
      page: 1,
      totalPages: null,
      lastHoveredRow: null,
      addRowHover: false,
      searchDebounce: null,
    }
  },
  computed: {
    addRowWidth() {
      return this.fields.length * 200 + 'px'
    },
    allFields() {
      return [].concat(this.primary || [], this.fields || [])
    },
    table() {
      const databaseType = DatabaseApplicationType.getType()
      for (const application of this.$store.getters['application/getAll']) {
        if (application.type !== databaseType) {
          continue
        }

        const foundTable = application.tables.find(
          ({ id }) => id === this.tableId
        )

        if (foundTable) {
          return foundTable
        }
      }

      return null
    },
  },
  async mounted() {
    // The first time we have to fetch the fields because they are unknown for this
    // table.
    if (!(await this.fetchFields(this.tableId))) {
      return false
    }

    // We want to start with some initial data when the modal opens for the first time.
    if (!(await this.fetch(1))) {
      return false
    }

    await this.orderFieldsByFirstGridViewFieldOptions(this.tableId)

    // Because most of the template depends on having some initial data we mark the
    // state as loaded after that. Only a loading animation is shown if there isn't any
    // data.
    this.loaded = true

    // Focus the search field so the user may begin typing immediately.
    this.$nextTick(() => {
      this.focusSearch()
    })
  },
  methods: {
    /**
     * Returns the scrollable element for the scrollbar.
     */
    getHorizontalScrollbarElement() {
      return this.$refs.right
    },
    /**
     * Event that is called when the users does any form of scrolling on the whole grid
     * surface.
     */
    scroll(pixelY, pixelX) {
      const left = this.$refs.right.scrollLeft + pixelX
      this.horizontalScroll(left)
      this.$refs.scrollbars.update()
    },
    horizontalScroll(left) {
      this.$refs.right.scrollLeft = left
    },
    /**
     * Returns true if the value already contains the given row id.
     */
    isAlreadySelected(rowId) {
      for (let i = 0; i < this.value.length; i++) {
        if (this.value[i].id === rowId) {
          return true
        }
      }
      return false
    },
    /**
     * Because the rows are split in a left and right section we need JavaScript to
     * show a hover effect of the whole row. This method makes sure the correct row has
     * the correct hover state.
     */
    setRowHover(row, value) {
      if (this.lastHoveredRow !== null && this.lastHoveredRow.id !== row.id) {
        this.lastHoveredRow._.hover = false
      }

      row._.hover = value
      this.lastHoveredRow = row
    },
    /**
     * Fetches all the fields of the given table id. We need the fields so that we can
     * show the data in the correct format.
     */
    async fetchFields(tableId) {
      try {
        const { data } = await FieldService(this.$client).fetchAll(tableId)
        data.forEach((part, index, d) => {
          populateField(data[index], this.$registry)
        })
        const primaryIndex = data.findIndex((item) => item.primary === true)
        this.primary =
          primaryIndex !== -1 ? data.splice(primaryIndex, 1)[0] : null
        this.fields = data
        return true
      } catch (error) {
        notifyIf(error, 'row')
        this.$emit('hide')
        this.loading = false
        return false
      }
    },
    /**
     * This method fetches the first grid and the related field options. The ordering
     * of that grid view will be applied to the already fetched fields. If anything
     * goes wrong or if there isn't a grid view, the original order will be used.
     */
    async orderFieldsByFirstGridViewFieldOptions(tableId) {
      try {
        const { data: views } = await ViewService(this.$client).fetchAll(
          tableId,
          false,
          false,
          false,
          // We can safely limit to `1` because the backend provides the views ordered.
          1,
          // We want to fetch the first grid view because for that type we're sure it's
          // compatible with `filterVisibleFieldsFunction` and
          // `sortFieldsByOrderAndIdFunction`. Others might also work, but this
          // component is styled like a grid view and it makes to most sense to reflect
          // that here.
          GridViewType.getType()
        )

        if (views.length === 0) {
          return
        }

        const {
          data: { field_options: fieldOptions },
        } = await ViewService(this.$client).fetchFieldOptions(views[0].id)
        this.fields = this.fields
          .filter(filterVisibleFieldsFunction(fieldOptions))
          .sort(sortFieldsByOrderAndIdFunction(fieldOptions))
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    /**
     * Does a row search in the table related to the state. It will also reset the
     * pagination.
     */
    doSearch(query, immediate) {
      const search = () => {
        this.search = query
        this.totalPages = null
        return this.fetch(1)
      }
      if (this.searchDebounce) {
        this.searchDebounce.cancel()
      }
      if (immediate) {
        search()
      } else {
        this.searchDebounce = debounce(search, 400)
        this.searchDebounce()
      }
    },
    /**
     * Fetches the rows of a given page and adds them to the state. If a search query
     * has been stored in the state then that will be remembered.
     */
    async fetch(page) {
      this.loading = true

      try {
        const { data } = await RowService(this.$client).fetchAll({
          tableId: this.tableId,
          page,
          size: 10,
          search: this.search,
        })
        data.results.forEach((part, index) => populateRow(data.results[index]))

        this.page = page
        this.totalPages = Math.ceil(data.count / 10)
        this.rows = data.results
        this.loading = false
        return true
      } catch (error) {
        notifyIf(error, 'row')
        this.$emit('hide')
        this.loading = false
        return false
      }
    },
    /**
     * Called when the user selects a row.
     */
    select(row, primary, fields) {
      if (this.isAlreadySelected(row.id)) {
        return
      }

      this.$emit('selected', { row, primary, fields })
    },
    /**
     * Focuses the search field when the component mounts.
     */
    focusSearch() {
      this.$refs.search?.focus()
    },
    async createRow({ row, callback }) {
      try {
        const preparedRow = prepareRowForRequest(
          row,
          this.allFields,
          this.$registry
        )

        const { data: rowCreated } = await RowService(this.$client).create(
          this.table.id,
          preparedRow
        )

        // When you create a new row from a linked row that links to its own table,the
        // realtime update will be sent from you, and you won't receive it.Since you
        // don't receive the realtime update we have to manually add the new row to the
        // state. We can do that by using the same function that is used by the
        // realtime update. (`viewType.rowCreated`)
        const view = this.$store.getters['view/getSelected']
        const viewType = this.$registry.get('view', view.type)
        viewType.rowCreated(
          { store: this.$store },
          this.table.id,
          this.allFields,
          rowCreated,
          {},
          'page/'
        )

        this.select(populateRow(rowCreated), this.primary, this.fields)

        callback()
      } catch (error) {
        callback(error)
      }
    },
  },
}
</script>
