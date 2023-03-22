<template>
  <div class="page-preview__wrapper">
    <div ref="preview" class="page-preview" :style="{ 'max-width': maxWidth }">
      <div ref="previewScaled" class="page-preview__scaled">
        <div ref="elementContainer">
          <ElementPreview
            v-for="(element, index) in elements"
            :key="element.id"
            :element="element"
            :active="element.id === elementSelectedId"
            :is-first-element="index === 0"
            :is-last-element="index === elements.length - 1"
            :is-copying="copyingElementIndex === index"
            @selected="selectElement(element)"
            @delete="deleteElement(element)"
            @move="moveElement(element, index, $event)"
            @insert="showAddElementModal(element, index, $event)"
            @copy="duplicateElement(element, index)"
          />
        </div>
      </div>
    </div>
    <AddElementModal
      ref="addElementModal"
      :adding-element-type="addingElementType"
      :page="page"
      @add="addElement"
    />
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import ElementPreview from '@baserow/modules/builder/components/elements/ElementPreview'
import { notifyIf } from '@baserow/modules/core/utils/error'
import AddElementModal from '@baserow/modules/builder/components/elements/AddElementModal'
import { PLACEMENTS } from '@baserow/modules/builder/enums'

export default {
  name: 'PagePreview',
  components: { AddElementModal, ElementPreview },
  data() {
    return {
      // This value is set when the insertion of a new element is in progress to
      // indicate where the element should be inserted
      beforeId: null,
      addingElementType: null,

      // The element that is currently being copied
      copyingElementIndex: null,
    }
  },
  computed: {
    ...mapGetters({
      page: 'page/getSelected',
      deviceTypeSelected: 'page/getDeviceTypeSelected',
      elementSelected: 'element/getSelected',
    }),
    elements() {
      return this.$store.getters['element/getElements']
    },
    elementSelectedId() {
      return this.elementSelected?.id
    },
    deviceType() {
      return this.deviceTypeSelected
        ? this.$registry.get('device', this.deviceTypeSelected)
        : null
    },
    maxWidth() {
      return this.deviceType?.maxWidth
        ? `${this.deviceType.maxWidth}px`
        : 'unset'
    },
  },
  watch: {
    deviceType(value) {
      this.$nextTick(() => {
        this.updatePreviewScale(value)
      })
    },
  },
  mounted() {
    window.addEventListener('resize', this.onWindowResized)
  },
  destroyed() {
    window.removeEventListener('resize', this.onWindowResized)
  },
  methods: {
    ...mapActions({
      actionCreateElement: 'element/create',
      actionCopyElement: 'element/copy',
      actionMoveElement: 'element/move',
      actionDeleteElement: 'element/delete',
      actionSelectElement: 'element/select',
    }),
    onWindowResized() {
      this.$nextTick(() => {
        this.updatePreviewScale(this.deviceType)
      })
    },
    updatePreviewScale(deviceType) {
      // The widths are the minimum width the preview must have. If the preview dom
      // element becomes smaller than the target, it will be scaled down so that the
      // actual width remains the same, and it will preview the correct device.
      const preview = this.$refs.preview
      const previewScaled = this.$refs.previewScaled

      const currentWidth = preview.clientWidth
      const currentHeight = preview.clientHeight
      const targetWidth = deviceType?.minWidth
      let scale = 1
      let horizontal = 0
      let vertical = 0

      if (currentWidth < targetWidth) {
        scale = Math.round((currentWidth / targetWidth) * 100) / 100
        horizontal = (currentWidth - currentWidth * scale) / 2 / scale
        vertical = (currentHeight - currentHeight * scale) / 2 / scale
      }

      previewScaled.style.transform = `scale(${scale})`
      previewScaled.style.transformOrigin = `0 0`
      previewScaled.style.width = `${horizontal * 2 + currentWidth}px`
      previewScaled.style.height = `${vertical * 2 + currentHeight}px`
    },
    async deleteElement(element) {
      try {
        await this.actionDeleteElement({
          elementId: element.id,
        })
      } catch (error) {
        notifyIf(error)
      }
    },
    moveElement(element, index, placement) {
      let elementToMoveId = null
      let beforeElementId = null

      if (placement === PLACEMENTS.BEFORE && index !== 0) {
        elementToMoveId = element.id
        beforeElementId = this.elements[index - 1].id
      } else if (
        placement === PLACEMENTS.AFTER &&
        index !== this.elements.length - 1
      ) {
        elementToMoveId = this.elements[index + 1].id
        beforeElementId = element.id
      }

      // If either is null then we are on the top or bottom end of the elements
      // and therefore the element can't be moved anymore
      if (elementToMoveId === null || beforeElementId === null) {
        return
      }

      try {
        this.actionMoveElement({
          pageId: this.page.id,
          elementId: elementToMoveId,
          beforeElementId,
        })
      } catch (error) {
        notifyIf(error)
      }
    },
    showAddElementModal(element, index, placement) {
      this.beforeId =
        placement === PLACEMENTS.BEFORE
          ? element.id
          : this.elements[index + 1]?.id
      this.$refs.addElementModal.show()
    },
    async addElement(elementType) {
      this.addingElementType = elementType.getType()
      try {
        await this.actionCreateElement({
          pageId: this.page.id,
          elementType: elementType.getType(),
          beforeId: this.beforeId,
        })
        this.$refs.addElementModal.hide()
      } catch (error) {
        notifyIf(error)
      }
      this.addingElementType = null
    },
    async duplicateElement(element, index) {
      this.copyingElementIndex = index
      try {
        await this.actionCopyElement({
          pageId: this.page.id,
          elementId: element.id,
        })
        this.$refs.addElementModal.hide()
      } catch (error) {
        notifyIf(error)
      }
      this.copyingElementIndex = null
    },
    selectElement(element) {
      this.actionSelectElement({ element })
    },
  },
}
</script>
