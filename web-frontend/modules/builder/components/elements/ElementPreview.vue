<template>
  <div
    :key="element.id"
    class="element-preview"
    :class="{
      'element-preview--active': isSelected,
      'element-preview--parent-of-selected': isParentOfSelectedElement,
      'element-preview--in-error': inError,
      'element-preview--first-element': isFirstElement,
      'element-preview--not-visible':
        !isVisible && !isSelected && !isParentOfSelectedElement,
    }"
    @click="onSelect"
  >
    <div v-if="isSelected" class="element-preview__name">
      {{ elementType.name }}
      <i v-if="!isVisible" class="iconoir-eye-off" />
    </div>
    <InsertElementButton
      v-show="isSelected"
      v-if="canCreate"
      class="element-preview__insert element-preview__insert--top"
      @click="showAddElementModal(PLACEMENTS.BEFORE)"
    />
    <ElementMenu
      v-if="isSelected && canUpdate"
      :placements="placements"
      :placements-disabled="placementsDisabled"
      :is-duplicating="isDuplicating"
      :has-parent="!!parentElement"
      @delete="deleteElement"
      @move="$emit('move', $event)"
      @duplicate="duplicateElement"
      @select-parent="selectParentElement()"
    />

    <PageElement
      :element="element"
      :mode="mode"
      class="element--read-only"
      :application-context-additions="applicationContextAdditions"
    />

    <InsertElementButton
      v-show="isSelected"
      v-if="canCreate"
      class="element-preview__insert element-preview__insert--bottom"
      @click="showAddElementModal(PLACEMENTS.AFTER)"
    />
    <AddElementModal
      v-if="canCreate"
      ref="addElementModal"
      :element-types-allowed="elementTypesAllowed"
      :page="page"
    />

    <i
      v-if="inError"
      class="element-preview__error-icon iconoir-warning-circle"
    ></i>
  </div>
</template>

<script>
import ElementMenu from '@baserow/modules/builder/components/elements/ElementMenu'
import InsertElementButton from '@baserow/modules/builder/components/elements/InsertElementButton'
import PageElement from '@baserow/modules/builder/components/page/PageElement'
import { PLACEMENTS } from '@baserow/modules/builder/enums'
import AddElementModal from '@baserow/modules/builder/components/elements/AddElementModal'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { mapActions, mapGetters } from 'vuex'
import { checkIntermediateElements } from '@baserow/modules/core/utils/dom'

export default {
  name: 'ElementPreview',
  components: {
    AddElementModal,
    ElementMenu,
    InsertElementButton,
    PageElement,
  },
  inject: ['workspace', 'builder', 'page', 'mode'],
  props: {
    element: {
      type: Object,
      required: true,
    },
    isLastElement: {
      type: Boolean,
      required: false,
      default: false,
    },
    isFirstElement: {
      type: Boolean,
      required: false,
      default: false,
    },
    isRootElement: {
      type: Boolean,
      required: false,
      default: false,
    },
    applicationContextAdditions: {
      type: Object,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      isDuplicating: false,
    }
  },
  computed: {
    ...mapGetters({
      elementSelected: 'element/getSelected',
      elementAncestors: 'element/getAncestors',
      getClosestSiblingElement: 'element/getClosestSiblingElement',
    }),
    isVisible() {
      switch (this.element.visibility) {
        case 'logged-in':
          return this.$store.getters['userSourceUser/isAuthenticated'](
            this.builder
          )
        case 'not-logged':
          return !this.$store.getters['userSourceUser/isAuthenticated'](
            this.builder
          )
        default:
          return true
      }
    },
    PLACEMENTS: () => PLACEMENTS,
    placements() {
      return [
        PLACEMENTS.BEFORE,
        PLACEMENTS.AFTER,
        PLACEMENTS.LEFT,
        PLACEMENTS.RIGHT,
      ]
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
    placementsDisabled() {
      const elementType = this.$registry.get('element', this.element.type)
      return elementType.getPlacementsDisabled(this.page, this.element)
    },
    elementTypesAllowed() {
      return (
        this.parentElementType?.childElementTypes(this.page, this.element) ||
        null
      )
    },
    canCreate() {
      return this.$hasPermission(
        'builder.page.create_element',
        this.page,
        this.workspace.id
      )
    },
    canUpdate() {
      return this.$hasPermission(
        'builder.page.element.update',
        this.element,
        this.workspace.id
      )
    },
    isSelected() {
      return this.element.id === this.elementSelected?.id
    },
    selectedElementAncestorIds() {
      if (!this.elementSelected) {
        return []
      }
      return this.elementAncestors(this.page, this.elementSelected).map(
        ({ id }) => id
      )
    },
    isParentOfSelectedElement() {
      return this.selectedElementAncestorIds.includes(this.element.id)
    },
    elementType() {
      return this.$registry.get('element', this.element.type)
    },
    parentElement() {
      if (!this.element.parent_element_id) {
        return null
      }
      return this.$store.getters['element/getElementById'](
        this.page,
        this.element.parent_element_id
      )
    },
    parentElementType() {
      return this.parentElement
        ? this.$registry.get('element', this.parentElement?.type)
        : null
    },
    nextElement() {
      return this.$store.getters['element/getNextElement'](
        this.page,
        this.element
      )
    },
    inError() {
      return this.elementType.isInError({
        element: this.element,
        builder: this.builder,
      })
    },
  },
  watch: {
    /**
     * If the element is currently selected, i.e. in the Elements Context menu,
     * ensure the element is scrolled into the viewport.
     */
    isSelected(newValue, old) {
      if (newValue && !old) {
        this.$el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    },
    /**
     * If the currently selected element in the Page Preview has moved, ensure
     * the element is scrolled into the viewport.
     */
    element: {
      handler(newValue, old) {
        if (
          (newValue.place_in_container !== old.place_in_container ||
            newValue.order !== old.order) &&
          this.isSelected
        ) {
          this.$el.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      },
      deep: true,
    },
  },
  mounted() {
    if (this.isFirstElement) {
      this.actionSelectElement({ element: this.element })
    }
  },
  methods: {
    ...mapActions({
      actionDuplicateElement: 'element/duplicate',
      actionDeleteElement: 'element/delete',
      actionSelectElement: 'element/select',
    }),
    onSelect($event) {
      // Here we check that the event has been emitted for this particular element
      // If we found an intermediate DOM element with the class `element-preview`,
      // or `element-preview__menu`, then we don't select the element.
      // It means it hasn't been originated by this element, so we don't select it.
      if (
        !checkIntermediateElements(this.$el, $event.target, (el) => {
          return (
            el.classList.contains('element-preview') ||
            el.classList.contains('element-preview__menu')
          )
        })
      ) {
        this.actionSelectElement({ element: this.element })
      }
    },
    showAddElementModal(placement) {
      this.$refs.addElementModal.show({
        placeInContainer: this.element.place_in_container,
        parentElementId: this.element.parent_element_id,
        beforeId: this.getBeforeId(placement),
      })
    },
    getBeforeId(placement) {
      return placement === PLACEMENTS.BEFORE
        ? this.element.id
        : this.nextElement?.id || null
    },
    async duplicateElement() {
      this.isDuplicating = true
      try {
        await this.actionDuplicateElement({
          page: this.page,
          elementId: this.element.id,
        })
      } catch (error) {
        notifyIf(error)
      }
      this.isDuplicating = false
    },
    async deleteElement() {
      try {
        const siblingElementToSelect = this.getClosestSiblingElement(
          this.page,
          this.elementSelected
        )
        await this.actionDeleteElement({
          page: this.page,
          elementId: this.element.id,
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
  },
}
</script>
