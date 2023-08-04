<template>
  <div class="page-preview__wrapper" @click.self="selectElement(null)">
    <PreviewNavigationBar :page="page" :style="{ maxWidth }" />
    <div ref="preview" class="page-preview" :style="{ maxWidth }">
      <div ref="previewScaled" class="page-preview__scaled">
        <ElementPreview
          v-for="(element, index) in elements"
          :key="element.id"
          :element="element"
          :page="page"
          :active="element.id === elementSelectedId"
          :is-first-element="index === 0"
          :is-last-element="index === elements.length - 1"
          :is-copying="copyingElementIndex === index"
          @selected="selectElement(element)"
          @delete="deleteElement(element)"
          @move="moveElement(element, index, $event)"
          @insert="showAddElementModal(element, index, $event)"
          @duplicate="duplicateElement(element, index)"
        />
      </div>
      <AddElementModal
        ref="addElementModal"
        :adding-element-type="addingElementType"
        :page="page"
        @add="addElement"
      />
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import ElementPreview from '@baserow/modules/builder/components/elements/ElementPreview'
import { notifyIf } from '@baserow/modules/core/utils/error'
import AddElementModal from '@baserow/modules/builder/components/elements/AddElementModal'
import PreviewNavigationBar from '@baserow/modules/builder/components/page/PreviewNavigationBar'
import { PLACEMENTS } from '@baserow/modules/builder/enums'

export default {
  name: 'PagePreview',
  components: { AddElementModal, ElementPreview, PreviewNavigationBar },
  data() {
    return {
      // This value is set when the insertion of a new element is in progress to
      // indicate where the element should be inserted
      beforeId: null,
      addingElementType: null,

      // The element that is currently being copied
      copyingElementIndex: null,

      // The resize observer to resize the preview when the wrapper size change
      resizeObserver: null,
    }
  },
  computed: {
    ...mapGetters({
      page: 'page/getSelected',
      deviceTypeSelected: 'page/getDeviceTypeSelected',
      elementSelected: 'element/getSelected',
      elements: 'element/getElements',
    }),
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
    this.resizeObserver = new ResizeObserver(() => {
      this.onWindowResized()
    })
    this.resizeObserver.observe(this.$el)
    this.onWindowResized()
  },
  destroyed() {
    this.resizeObserver.unobserve(this.$el)
  },
  methods: {
    ...mapActions({
      actionCreateElement: 'element/create',
      actionDuplicateElement: 'element/duplicate',
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

      const { clientWidth: currentWidth, clientHeight: currentHeight } =
        this.$refs.preview

      const targetWidth = deviceType?.minWidth
      let scale = 1

      if (currentWidth < targetWidth) {
        // Round scale at 2 decimals
        scale = Math.round((currentWidth / targetWidth) * 100) / 100
      }

      const previewScaled = this.$refs.previewScaled
      previewScaled.style.transform = `scale(${scale})`
      previewScaled.style.transformOrigin = `0 0`
      previewScaled.style.width = `${currentWidth / scale}px`
      previewScaled.style.height = `${currentHeight / scale}px`
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
      const elementToMoveId = element.id

      // BeforeElementId remains null if we are moving the element at the end of the
      // list
      let beforeElementId = null

      if (placement === PLACEMENTS.BEFORE) {
        beforeElementId = this.elements[index - 1].id
      } else if (index + 2 < this.elements.length) {
        beforeElementId = this.elements[index + 2].id
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
        await this.actionDuplicateElement({
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
