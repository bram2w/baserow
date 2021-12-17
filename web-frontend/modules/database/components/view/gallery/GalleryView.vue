<template>
  <div class="gallery-view">
    <a
      v-if="!readOnly"
      class="gallery-view__add"
      @click="$refs.rowCreateModal.show()"
    >
      <i class="fas fa-plus"></i>
    </a>
    <div ref="scroll" class="gallery-view__scroll">
      <div
        class="gallery-view__cards"
        :style="{
          height: height + 'px',
        }"
      >
        <RowCard
          v-for="slot in buffer"
          v-show="slot.left != -1"
          :key="'card-' + slot.id"
          :fields="cardFields"
          :row="slot.row === null ? {} : slot.row"
          :loading="slot.row === null"
          class="gallery-view__card"
          :style="{
            width: cardWidth + 'px',
            height: slot.row === null ? cardHeight + 'px' : undefined,
            transform: `translateX(${slot.left}px) translateY(${slot.top}px)`,
          }"
        ></RowCard>
      </div>
    </div>
    <RowCreateModal
      v-if="!readOnly"
      ref="rowCreateModal"
      :table="table"
      :fields="fields"
      :primary="primary"
      @created="createRow"
      @field-updated="$emit('refresh', $event)"
      @field-deleted="$emit('refresh')"
    ></RowCreateModal>
  </div>
</template>

<script>
import debounce from 'lodash/debounce'
import { mapGetters } from 'vuex'
import ResizeObserver from 'resize-observer-polyfill'

import { getCardHeight } from '@baserow/modules/database/utils/card'
import { maxPossibleOrderValue } from '@baserow/modules/database/viewTypes'
import RowCard from '@baserow/modules/database/components/card/RowCard'
import RowCreateModal from '@baserow/modules/database/components/row/RowCreateModal'

export default {
  name: 'GalleryView',
  components: { RowCard, RowCreateModal },
  props: {
    primary: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    database: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      gutterSize: 30,
      minimumCardWidth: 280,
      height: 0,
      cardWidth: 0,
      buffer: [],
    }
  },
  computed: {
    firstRows() {
      return this.allRows.slice(0, 200)
    },
    /**
     * In order for the virtual scrolling to work, we need to know what the height of
     * the card is to correctly position it.
     */
    cardHeight() {
      return getCardHeight(this.cardFields, this.$registry)
    },
    /**
     * Returns the visible field objects in the right order.
     */
    cardFields() {
      return [this.primary]
        .concat(this.fields)
        .filter((field) => {
          const exists = Object.prototype.hasOwnProperty.call(
            this.fieldOptions,
            field.id
          )
          return !exists || (exists && !this.fieldOptions[field.id].hidden)
        })
        .sort((a, b) => {
          const orderA = this.fieldOptions[a.id]
            ? this.fieldOptions[a.id].order
            : maxPossibleOrderValue
          const orderB = this.fieldOptions[b.id]
            ? this.fieldOptions[b.id].order
            : maxPossibleOrderValue

          // First by order.
          if (orderA > orderB) {
            return 1
          } else if (orderA < orderB) {
            return -1
          }

          // Then by id.
          if (a.id < b.id) {
            return -1
          } else if (a.id > b.id) {
            return 1
          } else {
            return 0
          }
        })
    },
  },
  watch: {
    cardHeight() {
      this.$nextTick(() => {
        this.updateBuffer()
      })
    },
    allRows() {
      this.$nextTick(() => {
        this.updateBuffer()
      })
    },
  },
  mounted() {
    this.updateBuffer()
    this.$el.resizeObserver = new ResizeObserver(() => {
      this.updateBuffer()
    })
    this.$el.resizeObserver.observe(this.$el)

    const fireUpdateBuffer = {
      last: Date.now(),
      distance: 0,
    }

    // Debounce function that's called when the user scrolls really fast. This is to
    // make sure that the `updateBuffer` method is called with the
    // `dispatchVisibleRows` parameter to true when the user immediately stops
    // scrolling fast.
    const updateBufferDebounced = debounce(() => {
      this.updateBuffer(true)
    }, 100)

    this.$el.scrollEvent = (event) => {
      const now = Date.now()
      const { scrollTop } = event.target

      const distance = Math.abs(scrollTop - fireUpdateBuffer.distance)
      const timeDelta = now - fireUpdateBuffer.last

      if (timeDelta > 100) {
        const velocity = distance / timeDelta

        fireUpdateBuffer.last = now
        fireUpdateBuffer.distance = scrollTop

        if (velocity < 2.5) {
          // When scrolling "slow", the dispatchVisibleRows parameter is true so that
          // the visible rows are fetched if needed.
          updateBufferDebounced.cancel()
          this.updateBuffer(true)
        } else {
          // Check if the user is scrolling super fast because in that case we don't
          // fetch the rows when they're not needed.
          updateBufferDebounced()
          this.updateBuffer(false)
        }
      } else {
        // If scroll stopped within the 100ms we still want to have a last
        // updateBuffer(true) call.
        updateBufferDebounced()
        this.updateBuffer(false)
      }
    }
    this.$refs.scroll.addEventListener('scroll', this.$el.scrollEvent)
  },
  beforeDestroy() {
    this.$el.resizeObserver.unobserve(this.$el)
    this.$refs.scroll.removeEventListener('scroll', this.$el.scrollEvent)
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        allRows: this.$options.propsData.storePrefix + 'view/gallery/getRows',
        fieldOptions:
          this.$options.propsData.storePrefix +
          'view/gallery/getAllFieldOptions',
      }),
    }
  },
  methods: {
    /**
     * This method makes sure that the correct cards/rows are shown based on the
     * scroll offset, viewport width, viewport height and card height. Based on these
     * values we can calculate which how many rows should be visible, which ones are
     * visible and what their position is without rendering all the rows in the store
     * at once.
     *
     * @TODO make this really virtual scrolling by letting the row persist in the same
     *   slot, even when it changes position. Currently, it updates all the cards when
     *   a new row of cards must be displayed.
     *
     * @param dispatchVisibleRows Indicates whether we want to dispatch the visibleRows
     *  action in the store. In some cases, when scrolling really fast through data we
     *  might want to wait a small moment before calling the action, which will make a
     *  request to the backend if needed.
     */
    updateBuffer(dispatchVisibleRows = true) {
      const el = this.$refs.scroll

      const gutterSize = this.gutterSize
      const containerWidth = el.clientWidth
      const containerHeight = el.clientHeight

      const cardsPerRow = Math.min(
        Math.max(Math.floor(containerWidth / this.minimumCardWidth), 1),
        20
      )
      const cardHeight = this.cardHeight
      const cardWidth = (containerWidth - gutterSize) / cardsPerRow - gutterSize
      const totalRows = Math.ceil(this.allRows.length / cardsPerRow)
      const height = totalRows * (cardHeight + gutterSize) + gutterSize

      this.cardWidth = cardWidth
      this.height = height

      const scrollTop = el.scrollTop
      const minimumCardsToRender =
        (Math.ceil(containerHeight / (cardHeight + gutterSize)) + 1) *
        cardsPerRow
      const startIndex =
        Math.floor(scrollTop / (cardHeight + gutterSize)) * cardsPerRow
      const endIndex = startIndex + minimumCardsToRender
      const visibleRows = this.allRows.slice(startIndex, endIndex)

      // Calculate an array containing only the rows that must be displayed and their
      // position in the gallery as if all the rows are there.
      this.buffer = visibleRows.map((row, positionInVisible) => {
        const positionInAll = startIndex + positionInVisible
        const left =
          gutterSize + (positionInAll % cardsPerRow) * (gutterSize + cardWidth)
        const top =
          gutterSize +
          Math.floor(positionInAll / cardsPerRow) * (gutterSize + cardHeight)

        return {
          id: positionInVisible,
          row,
          left,
          top,
        }
      })

      if (dispatchVisibleRows) {
        // Tell the store which rows/cards are visible so that it can fetch the missing
        // ones if needed.
        this.$store.dispatch(
          this.storePrefix + 'view/gallery/fetchMissingRowsInNewRange',
          {
            startIndex,
            endIndex,
          }
        )
      }
    },
    async createRow({ row, callback }) {
      try {
        await this.$store.dispatch(
          this.storePrefix + 'view/gallery/createNewRow',
          {
            view: this.view,
            table: this.table,
            fields: this.fields,
            primary: this.primary,
            values: row,
          }
        )
        callback()
      } catch (error) {
        callback(error)
      }
    },
  },
}
</script>
