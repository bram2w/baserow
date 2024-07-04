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
          v-for="childCurrent in childrenInColumn"
          :key="childCurrent.id"
          class="column-element__element"
        >
          <ElementPreview
            v-if="mode === 'editing'"
            :element="childCurrent"
            :application-context-additions="applicationContextAdditions"
            @move="move(childCurrent, $event)"
          ></ElementPreview>
          <PageElement
            v-else
            :element="childCurrent"
            :mode="mode"
            :application-context-additions="applicationContextAdditions"
          ></PageElement>
        </div>
      </template>
      <AddElementZone
        v-else-if="
          mode === 'editing' &&
          $hasPermission('builder.page.create_element', page, workspace.id)
        "
        @add-element="showAddElementModal(columnIndex)"
      />
    </div>
    <AddElementModal
      ref="addElementModal"
      :page="page"
      :element-types-allowed="elementType.childElementTypes(page, element)"
    />
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import _ from 'lodash'

import AddElementZone from '@baserow/modules/builder/components/elements/AddElementZone'
import AddElementModal from '@baserow/modules/builder/components/elements/AddElementModal'
import containerElement from '@baserow/modules/builder/mixins/containerElement'
import PageElement from '@baserow/modules/builder/components/page/PageElement'
import ElementPreview from '@baserow/modules/builder/components/elements/ElementPreview'
import { VERTICAL_ALIGNMENTS } from '@baserow/modules/builder/enums'
import { notifyIf } from '@baserow/modules/core/utils/error'
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
    applicationContextAdditions: {
      type: Object,
      required: false,
      default: null,
    },
  },
  computed: {
    flexAlignment() {
      const alignmentMapping = {
        [VERTICAL_ALIGNMENTS.TOP]: 'flex-start',
        [VERTICAL_ALIGNMENTS.CENTER]: 'center',
        [VERTICAL_ALIGNMENTS.BOTTOM]: 'flex-end',
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
    ...mapActions({
      actionMoveElement: 'element/moveElement',
    }),
    showAddElementModal(columnIndex) {
      this.$refs.addElementModal.show({
        placeInContainer: `${columnIndex}`,
        parentElementId: this.element.id,
      })
    },
    async move(element, placement) {
      try {
        await this.actionMoveElement({
          page: this.page,
          element,
          placement,
        })
      } catch (error) {
        notifyIf(error)
      }
    },
  },
}
</script>
