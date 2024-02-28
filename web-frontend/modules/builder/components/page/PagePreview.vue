<template>
  <ThemeProvider
    class="page-preview__wrapper"
    :class="`page-preview__wrapper--${deviceType.type}`"
    @click.self="actionSelectElement({ element: null })"
  >
    <PreviewNavigationBar :page="page" :style="{ maxWidth }" />
    <div ref="preview" class="page-preview" :style="{ 'max-width': maxWidth }">
      <div ref="previewScaled" class="page-preview__scaled">
        <CallToAction
          v-if="!elements.length"
          class="page-preview__empty"
          icon="baserow-icon-plus"
          icon-color="neutral"
          icon-size="large"
          icon-rounded
          @click="$refs.addElementModal.show()"
        >
          {{ $t('pagePreview.emptyMessage') }}
        </CallToAction>
        <AddElementModal ref="addElementModal" :page="page" />
        <ElementPreview
          v-for="(element, index) in elements"
          :key="element.id"
          is-root-element
          :element="element"
          :is-first-element="index === 0"
          :is-last-element="index === elements.length - 1"
          :placements="[PLACEMENTS.BEFORE, PLACEMENTS.AFTER]"
          :placements-disabled="getPlacementsDisabled(index)"
          :is-copying="copyingElementIndex === index"
          @move="moveElement(element, index, $event)"
        />
      </div>
    </div>
  </ThemeProvider>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import ElementPreview from '@baserow/modules/builder/components/elements/ElementPreview'
import { notifyIf } from '@baserow/modules/core/utils/error'
import PreviewNavigationBar from '@baserow/modules/builder/components/page/PreviewNavigationBar'
import { PLACEMENTS } from '@baserow/modules/builder/enums'
import AddElementModal from '@baserow/modules/builder/components/elements/AddElementModal.vue'
import ThemeProvider from '@baserow/modules/builder/components/theme/ThemeProvider.vue'

export default {
  name: 'PagePreview',
  components: {
    ThemeProvider,
    AddElementModal,
    ElementPreview,
    PreviewNavigationBar,
  },
  inject: ['page'],
  data() {
    return {
      // The element that is currently being copied
      copyingElementIndex: null,

      // The resize observer to resize the preview when the wrapper size change
      resizeObserver: null,
    }
  },
  computed: {
    PLACEMENTS: () => PLACEMENTS,
    ...mapGetters({
      deviceTypeSelected: 'page/getDeviceTypeSelected',
      elementSelected: 'element/getSelected',
    }),
    elements() {
      return this.$store.getters['element/getRootElements'](this.page)
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
      actionMoveElement: 'element/move',
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
    async moveElement(element, index, placement) {
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
        await this.actionMoveElement({
          page: this.page,
          elementId: elementToMoveId,
          beforeElementId,
        })
      } catch (error) {
        notifyIf(error)
      }
    },
    getPlacementsDisabled(index) {
      const placementsDisabled = []

      if (index === 0) {
        placementsDisabled.push(PLACEMENTS.BEFORE)
      }

      if (index === this.elements.length - 1) {
        placementsDisabled.push(PLACEMENTS.AFTER)
      }

      return placementsDisabled
    },
  },
}
</script>
