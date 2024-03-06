<template>
  <div
    class="column-element"
    :style="{
      '--space-between-columns': `${element.column_gap}px`,
      '--alignment': flexAlignment,
    }"
  >
    <div
      v-for="(childrenInColumn, columnIndex) in childrenElements"
      :key="columnIndex"
      class="column-element__column"
      :style="{ '--column-width': `${columnWidth}%` }"
    >
      <template v-if="childrenInColumn.length > 0">
        <div
          v-for="(childCurrent, rowIndex) in childrenInColumn"
          :key="childCurrent.id"
          class="column-element__element"
        >
          <ElementPreview
            v-if="mode === 'editing'"
            :element="childCurrent"
            :placements="[
              PLACEMENTS.BEFORE,
              PLACEMENTS.AFTER,
              PLACEMENTS.LEFT,
              PLACEMENTS.RIGHT,
            ]"
            :placements-disabled="getPlacementsDisabled(columnIndex, rowIndex)"
            @move="move(childCurrent, columnIndex, rowIndex, $event)"
          ></ElementPreview>
          <PageElement
            v-else
            :element="childCurrent"
            :mode="mode"
          ></PageElement>
        </div>
      </template>
      <AddElementZone
        v-else-if="mode === 'editing'"
        @add-element="showAddElementModal(columnIndex)"
      />
    </div>
    <AddElementModal
      ref="addElementModal"
      :page="page"
      :element-types-allowed="elementType.childElementTypes"
    />
  </div>
</template>

<script>
import AddElementZone from '@baserow/modules/builder/components/elements/AddElementZone'
import AddElementModal from '@baserow/modules/builder/components/elements/AddElementModal'
import containerElement from '@baserow/modules/builder/mixins/containerElement'
import PageElement from '@baserow/modules/builder/components/page/PageElement'
import ElementPreview from '@baserow/modules/builder/components/elements/ElementPreview'
import { PLACEMENTS, VERTICAL_ALIGNMENTS } from '@baserow/modules/builder/enums'
import { notifyIf } from '@baserow/modules/core/utils/error'
import _ from 'lodash'
import flushPromises from 'flush-promises'
import { dimensionMixin } from '@baserow/modules/core/mixins/dimensions'

export default {
  name: 'ColumnElement',
  components: {
    AddElementZone,
    ElementPreview,
    PageElement,
    AddElementModal,
  },
  mixins: [containerElement, dimensionMixin],
  props: {
    /**
     * @type {Object}
     * @property {number} column_amount - The amount of columns
     * @property {number} column_gap - The space between the columns
     * @property {string} alignment - The alignment of the columns
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    flexAlignment() {
      const alignmentMapping = {
        [VERTICAL_ALIGNMENTS.TOP.value]: 'start',
        [VERTICAL_ALIGNMENTS.CENTER.value]: 'center',
        [VERTICAL_ALIGNMENTS.BOTTOM.value]: 'end',
      }
      return alignmentMapping[this.element.alignment]
    },
    breakingPoint() {
      const minColumnWidth = 130
      const totalColumnWidth = minColumnWidth * this.element.column_amount
      const totalColumnGap =
        this.element.column_gap * (this.element.column_amount - 1)
      const extraPadding = 120

      return totalColumnWidth + totalColumnGap + extraPadding
    },
    columnAmount() {
      if (
        this.dimensions.width !== null &&
        this.dimensions.width < this.breakingPoint
      ) {
        return 1
      } else {
        return this.element.column_amount
      }
    },
    columnWidth() {
      return 100 / this.columnAmount - 0.00000000000001
    },
    childrenByColumnOrdered() {
      return _.groupBy(this.children, (child) => {
        const childCol = parseInt(child.place_in_container, 10)
        return childCol > this.columnAmount - 1
          ? this.columnAmount - 1
          : childCol
      })
    },
    childrenElements() {
      return [...Array(this.columnAmount).keys()].map(
        (columnIndex) => this.childrenByColumnOrdered[columnIndex] || []
      )
    },
  },
  mounted() {
    this.dimensions.targetElement = this.$el.parentElement
  },
  methods: {
    showAddElementModal(columnIndex) {
      this.$refs.addElementModal.show({
        placeInContainer: `${columnIndex}`,
        parentElementId: this.element.id,
      })
    },
    getPlacementsDisabled(columnIndex, rowIndex) {
      const placementsDisabled = []

      if (columnIndex === 0) {
        placementsDisabled.push(PLACEMENTS.LEFT)
      }

      if (columnIndex === this.columnAmount - 1) {
        placementsDisabled.push(PLACEMENTS.RIGHT)
      }

      if (rowIndex === 0) {
        placementsDisabled.push(PLACEMENTS.BEFORE)
      }

      if (rowIndex === this.childrenByColumnOrdered[columnIndex].length - 1) {
        placementsDisabled.push(PLACEMENTS.AFTER)
      }

      return placementsDisabled
    },
    async move(element, columnIndex, rowIndex, placement) {
      // Wait for the event propagation to be stopped by the child element otherwise
      // the click event select the container because the element is removed from the
      // DOM too quickly
      await flushPromises()

      if (placement === PLACEMENTS.AFTER || placement === PLACEMENTS.BEFORE) {
        await this.moveVertical(element, rowIndex, columnIndex, placement)
      } else {
        await this.moveHorizontal(element, columnIndex, placement)
      }
    },
    async moveVertical(element, rowIndex, columnIndex, placement) {
      const elementsInColumn = this.childrenByColumnOrdered[columnIndex]
      const elementToMoveId = element.id

      // BeforeElementId remains null if we are moving the element at the end of the
      // list
      let beforeElementId = null

      if (placement === PLACEMENTS.BEFORE) {
        beforeElementId = elementsInColumn[rowIndex - 1].id
      } else if (rowIndex + 2 < elementsInColumn.length) {
        beforeElementId = elementsInColumn[rowIndex + 2].id
      }

      try {
        await this.actionMoveElement({
          page: this.page,
          elementId: elementToMoveId,
          beforeElementId,
          parentElementId: this.element.id,
          placeInContainer: element.place_in_container,
        })
      } catch (error) {
        notifyIf(error)
      }
    },
    async moveHorizontal(element, columnIndex, placement) {
      const placeInContainer = parseInt(element.place_in_container)
      const newPlaceInContainer =
        placement === PLACEMENTS.LEFT
          ? placeInContainer - 1
          : placeInContainer + 1

      if (newPlaceInContainer >= 0) {
        try {
          await this.actionMoveElement({
            page: this.page,
            elementId: element.id,
            beforeElementId: null,
            parentElementId: this.element.id,
            placeInContainer: `${newPlaceInContainer}`,
          })
        } catch (error) {
          notifyIf(error)
        }
      }
    },
  },
}
</script>
