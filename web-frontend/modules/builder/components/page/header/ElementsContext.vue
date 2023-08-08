<template>
  <Context>
    <div class="select elements-context">
      <div class="select__search">
        <i class="select__search-icon fas fa-search"></i>
        <input
          v-model="search"
          type="text"
          class="select__search-input"
          :placeholder="$t('elementsContext.searchPlaceholder')"
        />
      </div>
      <ElementsList
        v-if="elementsMatchingSearchTerm.length"
        :elements="elementsMatchingSearchTerm"
        :element-selected="elementSelected"
        @select="selectElement($event)"
      />
      <div class="select__footer">
        <div class="select__footer-create">
          <AddElementButton
            :class="{
              'margin-top-1': elementsMatchingSearchTerm.length === 0,
            }"
            @click="$refs.addElementModal.show()"
          />
        </div>
      </div>
    </div>
    <AddElementModal
      ref="addElementModal"
      :page="page"
      @element-added="onElementAdded"
    />
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import ElementsList from '@baserow/modules/builder/components/elements/ElementsList'
import AddElementButton from '@baserow/modules/builder/components/elements/AddElementButton'
import AddElementModal from '@baserow/modules/builder/components/elements/AddElementModal'
import { mapActions, mapGetters } from 'vuex'
import { isSubstringOfStrings } from '@baserow/modules/core/utils/string'

export default {
  name: 'ElementsContext',
  components: { AddElementModal, AddElementButton, ElementsList },
  mixins: [context],
  data() {
    return {
      search: null,
      addingElementType: null,
    }
  },
  computed: {
    ...mapGetters({
      page: 'page/getSelected',
      elements: 'element/getRootElements',
      elementSelected: 'element/getSelected',
    }),
    elementsMatchingSearchTerm() {
      if (
        this.search === '' ||
        this.search === null ||
        this.search === undefined
      ) {
        return this.elements
      }

      return this.elements.filter((element) => {
        const elementType = this.$registry.get('element', element.type)
        return isSubstringOfStrings([elementType.name], this.search)
      })
    },
  },
  methods: {
    ...mapActions({
      actionSelectElement: 'element/select',
    }),
    onElementAdded() {
      this.hide()
    },
    selectElement(element) {
      this.actionSelectElement({ element })
      this.hide()
    },
  },
}
</script>
