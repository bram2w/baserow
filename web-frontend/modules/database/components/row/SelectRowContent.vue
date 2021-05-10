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
          v-model="visibleSearch"
          type="text"
          placeholder="Search rows"
          class="input select-row-modal__search-input"
          @keypress.enter="doSearch(visibleSearch)"
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
          </div>
          <div
            class="select-row-modal__foot"
            :style="{
              width: 3 * 200 + 'px',
            }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import FieldService from '@baserow/modules/database/services/field'
import { populateField } from '@baserow/modules/database/store/field'
import RowService from '@baserow/modules/database/services/row'
import { populateRow } from '@baserow/modules/database/store/view/grid'

import Paginator from '@baserow/modules/core/components/Paginator'
import SelectRowField from './SelectRowField'

export default {
  name: 'SelectRowContent',
  components: { Paginator, SelectRowField },
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
    }
  },
  async mounted() {
    // The first time we have to fetch the fields because they are unknown for this
    // table.
    await this.fetchFields(this.tableId)

    // We want to start with some initial data when the modal opens for the first time.
    await this.fetch(1)

    // Becuase most of the template depends on having some initial data we mark the
    // state as loaded after that. Only a loading animation is shown if there isn't any
    // data.
    this.loaded = true
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
     * Because the rows are split in a left and right section we need Javascript to
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
      } catch (error) {
        this.loading = false
        notifyIf(error, 'row')
      }
    },
    /**
     * Does a row search in the table related to the state. It will also reset the
     * pagination.
     */
    async doSearch(query) {
      this.search = query
      this.totalPages = null
      await this.fetch(1)
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
      } catch (error) {
        notifyIf(error, 'row')
      }

      this.loading = false
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
  },
}
</script>
