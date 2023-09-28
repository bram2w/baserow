<template>
  <Context
    class="select elements-context"
    :max-height-if-outside-viewport="true"
  >
    <div class="select__search">
      <i class="select__search-icon iconoir-search"></i>
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
    <div v-else class="context__description">
      {{ $t('elementsContext.noElements') }}
    </div>
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
  inject: ['page'],
  data() {
    return {
      search: null,
      addingElementType: null,
    }
  },
  computed: {
    ...mapGetters({
      elementSelected: 'element/getSelected',
    }),
    elements() {
      return this.$store.getters['element/getRootElements'](this.page)
    },
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
