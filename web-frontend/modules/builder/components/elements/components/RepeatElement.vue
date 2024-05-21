<template>
  <div>
    <!-- If we have any contents to repeat... -->
    <template v-if="elementContent.length > 0">
      <!-- Iterate over each content -->
      <div v-for="(content, index) in elementContent" :key="content.id">
        <!-- If the container has an children -->
        <template v-if="children.length > 0">
          <!-- Iterate over each child -->
          <template v-for="child in children">
            <!-- The first iteration is editable if we're in editing mode -->
            <ElementPreview
              v-if="index === 0 && isEditMode"
              :key="child.id"
              :element="child"
              @move="moveElement(child, $event)"
            />
            <!-- Other iterations are not editable -->
            <!-- Override the mode so that any children are in preview mode -->
            <PageElement
              v-else
              :key="child.id"
              :element="child"
              :force-mode="'preview'"
              :class="{
                'repeat-element-preview': index > 0 && isEditMode,
              }"
            />
          </template>
        </template>
      </div>
      <!-- We have contents, but the container has no children... -->
      <template v-if="children.length === 0 && isEditMode">
        <!-- Give the designer the chance to add child elements -->
        <AddElementZone @add-element="showAddElementModal"></AddElementZone>
        <AddElementModal
          ref="addElementModal"
          :page="page"
          :element-types-allowed="elementType.childElementTypes"
        ></AddElementModal>
      </template>
    </template>
    <!-- We have no contents to repeat -->
    <template v-else>
      <!-- If we also have no children, allow the designer to add elements -->
      <template v-if="children.length === 0 && isEditMode">
        <AddElementZone @add-element="showAddElementModal"></AddElementZone>
        <AddElementModal
          ref="addElementModal"
          :page="page"
          :element-types-allowed="elementType.childElementTypes"
        ></AddElementModal>
      </template>
      <!-- We have no contents, but we do have children in edit mode -->
      <template v-else-if="isEditMode">
        <ElementPreview
          v-for="child in children"
          :key="child.id"
          :element="child"
          @move="moveElement(child, $event)"
        />
      </template>
    </template>
    <div class="repeat-element__footer">
      <ABButton
        v-if="hasMorePage && children.length > 0"
        :disabled="contentLoading"
        :loading="contentLoading"
        @click="loadMore()"
      >
        {{ $t('repeatElement.showMore') }}
      </ABButton>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

import AddElementZone from '@baserow/modules/builder/components/elements/AddElementZone'
import containerElement from '@baserow/modules/builder/mixins/containerElement'
import collectionElement from '@baserow/modules/builder/mixins/collectionElement'
import AddElementModal from '@baserow/modules/builder/components/elements/AddElementModal'
import ElementPreview from '@baserow/modules/builder/components/elements/ElementPreview'
import PageElement from '@baserow/modules/builder/components/page/PageElement'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'RepeatElement',
  components: {
    PageElement,
    ElementPreview,
    AddElementModal,
    AddElementZone,
  },
  mixins: [containerElement, collectionElement],
  props: {
    /**
     * @type {Object}
     * @property {int} data_source_id - The collection data source Id we want to display.
     * @property {int} items_per_page - The number of items per page.
     */
    element: {
      type: Object,
      required: true,
    },
  },
  methods: {
    ...mapActions({
      actionMoveElement: 'element/moveElement',
    }),
    showAddElementModal() {
      this.$refs.addElementModal.show({
        placeInContainer: null,
        parentElementId: this.element.id,
      })
    },
    async moveElement(element, placement) {
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
