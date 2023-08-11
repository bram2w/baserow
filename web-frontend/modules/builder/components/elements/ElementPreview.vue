<template>
  <div
    class="element-preview"
    :class="{
      'element-preview--active': isSelected,
      'element-preview--in-error': inError,
    }"
    @click.stop="actionSelectElement({ element })"
  >
    <InsertElementButton
      v-if="isSelected"
      class="element-preview__insert--top"
      @click="showAddElementModal(PLACEMENTS.BEFORE)"
    />
    <ElementMenu
      v-if="isSelected"
      :placements="placements"
      :placements-disabled="placementsDisabled"
      :is-duplicating="isDuplicating"
      @delete="deleteElement"
      @move="$emit('move', $event)"
      @duplicate="duplicateElement"
    />

    <PageRootElement
      v-if="isRootElement"
      :element="element"
      :mode="mode"
    ></PageRootElement>
    <PageElement v-else :element="element" :mode="mode" />

    <InsertElementButton
      v-if="isSelected"
      class="element-preview__insert--bottom"
      @click="showAddElementModal(PLACEMENTS.AFTER)"
    />
    <AddElementModal
      ref="addElementModal"
      :element-types-allowed="elementTypesAllowed"
      :page="page"
    />
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
import PageRootElement from '@baserow/modules/builder/components/page/PageRootElement'

export default {
  name: 'ElementPreview',
  components: {
    AddElementModal,
    ElementMenu,
    InsertElementButton,
    PageElement,
    PageRootElement,
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
  computed: {
    ...mapGetters({ elementSelected: 'element/getSelected' }),
    PLACEMENTS: () => PLACEMENTS,
    elementTypesAllowed() {
      return this.parentElementType?.childElementTypes || null
    },
    isSelected() {
      return this.element.id === this.elementSelected?.id
    },
    elementType() {
      return this.$registry.get('element', this.element.type)
    },
    parentElement() {
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
  },
}
</script>
