<template>
  <Context
    class="select elements-context"
    max-height-if-outside-viewport
    @shown="shown()"
  >
    <div class="select__search">
      <i class="select__search-icon iconoir-search"></i>
      <input
        ref="search"
        v-model="search"
        type="text"
        class="elements-list__search-input"
        :placeholder="$t('elementsContext.searchPlaceholder')"
      />
    </div>
    <ElementsList
      v-if="elementsVisible"
      :elements="rootElements"
      :filtered-search-elements="filteredSearchElements"
      @select="selectElement($event)"
    />
    <div v-else class="context__description">
      {{ $t('elementsContext.noElements') }}
    </div>
    <div
      v-if="$hasPermission('builder.page.create_element', page, workspace.id)"
      class="elements-list__footer"
    >
      <div class="elements-list__footer-create">
        <AddElementButton
          :class="{
            'margin-top-1': !elementsVisible,
          }"
          @click="$refs.addElementModal.show()"
        />
      </div>
    </div>
    <AddElementModal
      v-if="$hasPermission('builder.page.create_element', page, workspace.id)"
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
import { mapActions } from 'vuex'
import { isSubstringOfStrings } from '@baserow/modules/core/utils/string'

export default {
  name: 'ElementsContext',
  components: { AddElementModal, AddElementButton, ElementsList },
  mixins: [context],
  inject: ['workspace', 'page', 'builder', 'mode'],
  data() {
    return {
      search: null,
      addingElementType: null,
    }
  },
  computed: {
    elementsVisible() {
      return (
        (this.search && this.filteredSearchElements.length) ||
        (!this.search && this.rootElements.length)
      )
    },
    rootElements() {
      return this.$store.getters['element/getRootElements'](this.page)
    },
    /*
     * When a user searches for elements in the list, this computed method
     * is responsible for finding *all* matching elements, and then finding
     * each ancestor of those elements. This ensures that we only display
     * elements in tree until our matching element is found. For example, a
     * tree such as the following:
     *
     * - Repeat
     *     - Column
     *         - Heading 1
     *         - Repeat
     *             - Image
     *         - Heading 2
     *
     * With a search query of "heading" would result in:
     *
     * - Repeat
     *     - Column
     *         - Heading 1
     *         - Heading 2
     *
     * With a search query of "image" would result in:
     *
     * - Repeat
     *     - Column
     *         - Repeat
     *             - Image
     */
    filteredSearchElements() {
      let filteredToElementIds = []
      if (
        this.search === '' ||
        this.search === null ||
        this.search === undefined
      ) {
        // If there's no search query, then there are no
        // elements to narrow the results down to.
        return filteredToElementIds
      }

      // Iterate over all the root-level elements.
      this.rootElements.forEach((rootElement) => {
        // Find this element's descendants and loop over them.
        const descendants = this.$store.getters['element/getDescendants'](
          this.page,
          rootElement
        )
        descendants.forEach((descendant) => {
          // Build this descendant's corpus (for now, display name only)
          // and check if it matches the search query.
          const descendantCorpus = this.getElementCorpus(descendant)
          if (isSubstringOfStrings([descendantCorpus], this.search)) {
            // The descendant matches. We need to include *this* element,
            // and all its *ancestors* in our list of narrowed results.
            const ascendants = this.$store.getters['element/getAncestors'](
              this.page,
              descendant
            )
            filteredToElementIds.push(descendant.id)
            filteredToElementIds = filteredToElementIds.concat(
              ascendants.map((a) => a.id)
            )
          }
        })

        // Test of the root element itself matches the search query.
        // if it does, it gets included in the narrowed results too.
        const rootCorpus = this.getElementCorpus(rootElement)
        if (isSubstringOfStrings([rootCorpus], this.search)) {
          // The root element matches.
          filteredToElementIds.push(rootElement.id)
        }
      })
      filteredToElementIds = [...new Set(filteredToElementIds)]
      return filteredToElementIds
    },
  },
  methods: {
    ...mapActions({
      actionSelectElement: 'element/select',
    }),
    /*
     * Given an element, this method will return the corpus we want to
     * search against when a user enters a search query. Should we want
     * to search both the 'display name' and the element type name, this
     * method can be easily adapted to combine the two and return it.
     */
    getElementCorpus(element) {
      const elementType = this.$registry.get('element', element.type)
      return elementType.getDisplayName(element, {
        builder: this.builder,
        page: this.page,
        mode: this.mode,
        element,
      })
    },
    onElementAdded() {
      this.hide()
    },
    selectElement(element) {
      this.actionSelectElement({ element })
      this.hide()
    },
    shown() {
      this.search = null
      this.$nextTick(() => {
        this.$refs.search.focus()
      })
    },
  },
}
</script>
