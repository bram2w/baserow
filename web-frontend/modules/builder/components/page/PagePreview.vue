<template>
  <ThemeProvider
    class="page-preview__wrapper"
    :class="`page-preview__wrapper--${deviceType.type}`"
    @click.self="actionSelectElement({ element: null })"
  >
    <PreviewNavigationBar :page="page" :style="{ maxWidth }" />
    <div ref="preview" class="page-preview" :style="{ 'max-width': maxWidth }">
      <div
        ref="previewScaled"
        class="page-preview__scaled"
        tabindex="0"
        @keydown="handleKeyDown"
      >
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
        <div v-else class="page">
          <ElementPreview
            v-for="(element, index) in elements"
            :key="element.id"
            is-root-element
            :element="element"
            :is-first-element="index === 0"
            :is-last-element="index === elements.length - 1"
            :is-copying="copyingElementIndex === index"
            :application-context-additions="{
              recordIndexPath: [],
            }"
            @move="moveElement($event)"
          />
        </div>
      </div>
      <AddElementModal ref="addElementModal" :page="page" />
    </div>
  </ThemeProvider>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'

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
  inject: ['page', 'workspace'],
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
      getChildren: 'element/getChildren',
      getClosestSiblingElement: 'element/getClosestSiblingElement',
    }),
    elements() {
      return this.$store.getters['element/getRootElements'](this.page)
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
    parentOfElementSelected() {
      if (!this.elementSelected?.parent_element_id) {
        return null
      }
      return this.$store.getters['element/getElementById'](
        this.page,
        this.elementSelected.parent_element_id
      )
    },
    canCreateElement() {
      return this.$hasPermission(
        'builder.page.create_element',
        this.page,
        this.workspace.id
      )
    },
    canUpdateSelectedElement() {
      return this.$hasPermission(
        'builder.page.element.update',
        this.elementSelected,
        this.workspace.id
      )
    },
    canDeleteSelectedElement() {
      return this.$hasPermission(
        'builder.page.element.delete',
        this.elementSelected,
        this.workspace.id
      )
    },
  },
  watch: {
    deviceType(value) {
      this.$nextTick(() => {
        this.updatePreviewScale(value)
      })
    },
    elementSelectedId(newValue) {
      if (newValue) {
        this.$refs.previewScaled.focus()
      }
    },
  },
  mounted() {
    this.resizeObserver = new ResizeObserver(() => {
      this.onWindowResized()
    })
    this.resizeObserver.observe(this.$el)
    this.onWindowResized()

    document.addEventListener('keydown', this.preventScrollIfFocused)
  },
  destroyed() {
    this.resizeObserver.unobserve(this.$el)
    document.removeEventListener('keydown', this.preventScrollIfFocused)
  },
  methods: {
    ...mapActions({
      actionDuplicateElement: 'element/duplicate',
      actionDeleteElement: 'element/delete',
      actionMoveElement: 'element/moveElement',
      actionSelectElement: 'element/select',
      actionSelectNextElement: 'element/selectNextElement',
    }),
    preventScrollIfFocused(e) {
      if (this.$refs.previewScaled === document.activeElement) {
        switch (e.key) {
          case 'ArrowLeft':
          case 'ArrowRight':
          case 'ArrowUp':
          case 'ArrowDown':
            e.preventDefault()
            break
        }
      }
    },
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

    async moveElement(placement) {
      if (!this.elementSelected?.id || !this.canUpdateSelectedElement) {
        return
      }

      const elementType = this.$registry.get(
        'element',
        this.elementSelected.type
      )
      const placementsDisabled = elementType.getPlacementsDisabled(
        this.page,
        this.elementSelected
      )

      if (placementsDisabled.includes(placement)) {
        return
      }

      try {
        await this.actionMoveElement({
          page: this.page,
          element: this.elementSelected,
          placement,
        })
        await this.actionSelectElement({ element: this.elementSelected })
      } catch (error) {
        notifyIf(error)
      }
    },
    async selectNextElement(placement) {
      if (!this.elementSelected?.id) {
        return
      }

      const elementType = this.$registry.get(
        'element',
        this.elementSelected.type
      )
      const placementsDisabled = elementType.getPlacementsDisabled(
        this.page,
        this.elementSelected
      )

      if (placementsDisabled.includes(placement)) {
        return
      }

      try {
        await this.actionSelectNextElement({
          page: this.page,
          element: this.elementSelected,
          placement,
        })
      } catch (error) {
        notifyIf(error)
      }
    },
    async duplicateElement() {
      if (!this.elementSelected?.id || !this.canCreateElement) {
        return
      }

      this.isDuplicating = true
      try {
        await this.actionDuplicateElement({
          page: this.page,
          elementId: this.elementSelected.id,
        })
      } catch (error) {
        notifyIf(error)
      }
      this.isDuplicating = false
    },
    async deleteElement() {
      if (!this.elementSelected?.id || !this.canDeleteSelectedElement) {
        return
      }
      try {
        const siblingElementToSelect = this.getClosestSiblingElement(
          this.page,
          this.elementSelected
        )
        await this.actionDeleteElement({
          page: this.page,
          elementId: this.elementSelected.id,
        })
        if (siblingElementToSelect?.id) {
          await this.actionSelectElement({ element: siblingElementToSelect })
        }
      } catch (error) {
        notifyIf(error)
      }
    },
    selectParentElement() {
      if (this.parentOfElementSelected) {
        this.actionSelectElement({ element: this.parentOfElementSelected })
      }
    },
    selectChildElement() {
      const children = this.getChildren(this.page, this.elementSelected)
      if (children.length) {
        this.actionSelectElement({ element: children[0] })
      }
    },
    handleKeyDown(e) {
      let shouldPrevent = true
      const alternateAction = e.altKey || e.ctrlKey || e.metaKey
      switch (e.key) {
        case 'ArrowUp':
          if (alternateAction) {
            this.moveElement(PLACEMENTS.BEFORE)
          } else {
            this.selectNextElement(PLACEMENTS.BEFORE)
          }
          break
        case 'ArrowDown':
          if (alternateAction) {
            this.moveElement(PLACEMENTS.AFTER)
          } else {
            this.selectNextElement(PLACEMENTS.AFTER)
          }
          break
        case 'ArrowLeft':
          if (alternateAction) {
            this.moveElement(PLACEMENTS.LEFT)
          } else {
            this.selectNextElement(PLACEMENTS.LEFT)
          }
          break
        case 'ArrowRight':
          if (alternateAction) {
            this.moveElement(PLACEMENTS.RIGHT)
          } else {
            this.selectNextElement(PLACEMENTS.RIGHT)
          }
          break
        case 'Backspace':
        case 'Clear':
        case 'Delete':
          this.deleteElement()
          break
        case 'c':
          this.selectChildElement()
          break
        case 'd':
          this.duplicateElement()
          break
        case 'p':
          this.selectParentElement()
          break
        default:
          shouldPrevent = false
      }
      if (shouldPrevent) {
        e.stopPropagation()
        e.preventDefault()
      }
    },
  },
}
</script>
