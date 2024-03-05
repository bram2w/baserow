<template>
  <div
    :key="element.id"
    class="element-preview"
    :class="{
      'element-preview--active': isSelected,
      'element-preview--parent-of-selected': isParentOfSelectedElement,
      'element-preview--in-error': inError,
      'element-preview--first-element': isFirstElement,
    }"
    tabindex="0"
    @click="onSelect"
    @keyup.d.stop="duplicateElement"
    @keyup.delete.stop="deleteElement"
    @keyup.p.stop="selectParentElement"
  >
    <InsertElementButton
      v-show="isSelected"
      class="element-preview__insert element-preview__insert--top"
      @click="showAddElementModal(PLACEMENTS.BEFORE)"
    />
    <ElementMenu
      v-if="isSelected"
      :placements="placements"
      :placements-disabled="placementsDisabled"
      :is-duplicating="isDuplicating"
      :has-parent="!!parentElement"
      @delete="deleteElement"
      @move="$emit('move', $event)"
      @duplicate="duplicateElement"
      @select-parent="actionSelectElement({ element: parentElement })"
    />

    <PageElement :element="element" :mode="mode" class="element--read-only" />

    <InsertElementButton
      v-show="isSelected"
      class="element-preview__insert element-preview__insert--bottom"
      @click="showAddElementModal(PLACEMENTS.AFTER)"
    />
    <AddElementModal
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
  inject: ['builder', 'page', 'mode'],
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
    placements: {
      type: Array,
      required: false,
      default: () => [PLACEMENTS.BEFORE, PLACEMENTS.AFTER],
    },
    placementsDisabled: {
      type: Array,
      required: false,
      default: () => [],
    },
    isRootElement: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      isDuplicating: false,
    }
  },
  watch: {
    /**
     * Focuses the element if the element has been selected.
     */
    isSelected(newValue, old) {
      if (newValue && !old) {
        this.$el.focus()
      }
    },
  },
  computed: {
    ...mapGetters({
      elementSelected: 'element/getSelected',
      elementAncestors: 'element/getAncestors',
    }),
    PLACEMENTS: () => PLACEMENTS,
    elementTypesAllowed() {
      return this.parentElementType?.childElementTypes || null
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
    siblingElements() {
      return this.$store.getters['element/getSiblings'](this.page, this.element)
    },
    samePlaceInContainerElements() {
      return this.siblingElements.filter(
        (e) => e.place_in_container === this.element.place_in_container
      )
    },
    nextElement() {
      return [...this.samePlaceInContainerElements].find((e) =>
        e.order.gt(this.element.order)
      )
    },
    inError() {
      return this.elementType.isInError({
        element: this.element,
        builder: this.builder,
      })
    },
  },
  methods: {
    ...mapActions({
      actionDuplicateElement: 'element/duplicate',
      actionDeleteElement: 'element/delete',
      actionSelectElement: 'element/select',
    }),
    onSelect($event) {
      // Here we check that the event has been emitted for this particular element
      // If we found an intermediate DOM element with the class `element-preview`
      // It means it hasn't been originated by this element so we don't select it.
      if (
        !checkIntermediateElements(this.$el, $event.target, (el) => {
          return el.classList.contains('element-preview')
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
        await this.actionDeleteElement({
          page: this.page,
          elementId: this.element.id,
        })
      } catch (error) {
        notifyIf(error)
      }
    },
    selectParentElement() {
      if (this.parentElement) {
        this.actionSelectElement({ element: this.parentElement })
      }
    },
  },
}
</script>
