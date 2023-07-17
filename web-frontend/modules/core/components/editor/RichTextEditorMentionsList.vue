<template>
  <div
    class="dropdown rich-text-editor__mention-dropdown"
    :class="{
      'dropdown--floating': !showInput,
      'dropdown--disabled': disabled,
    }"
    :tabindex="realTabindex"
    @contextmenu.stop
    @focusin="show()"
    @focusout="focusout($event)"
  >
    <div class="dropdown__items" :class="{ hidden: !open }">
      <ul
        ref="items"
        v-prevent-parent-scroll
        v-auto-overflow-scroll
        class="select__items"
        tabindex=""
        @scroll="scroll"
      >
        <FieldCollaboratorDropdownItem
          v-for="collaborator in results"
          :key="collaborator.user_id"
          :name="collaborator.name"
          :value="collaborator.user_id"
        ></FieldCollaboratorDropdownItem>
      </ul>
      <div v-show="isNotFound" class="select__description">
        {{ notFoundErrorMessage }}
      </div>
    </div>
  </div>
</template>

<script>
import inMemoryPaginatedDropdown from '@baserow/modules/core/mixins/inMemoryPaginatedDropdown'
import FieldCollaboratorDropdownItem from '@baserow/modules/database/components/field/FieldCollaboratorDropdownItem'

export default {
  name: 'RichTextEditorMentionsList',
  components: { FieldCollaboratorDropdownItem },
  mixins: [inMemoryPaginatedDropdown],
  props: {
    collaborators: {
      type: Array,
      required: true,
    },
    command: {
      type: Function,
      required: true,
    },
  },
  computed: {
    isNotFound() {
      return this.results.length === 0
    },
    notFoundErrorMessage() {
      // Must use $options for it to work in the saas, something to do with how this
      // is manually rendered...
      return this.$options.$i18n.t('richTextEditorMentionsList.notFound')
    },
  },
  watch: {
    collaborators() {
      this.search()
      this.hoverFirstItem()
    },
  },
  mounted() {
    this.hoverFirstItem()
  },
  methods: {
    hoverFirstItem() {
      this.$nextTick(() => {
        this.hover = this.collaborators[0]?.user_id
      })
    },
    filterItems() {
      // No need to filter items because `suggestion` filters them already.
      return this.collaborators
    },
    onKeyDown({ event }) {
      if (this.open) {
        // return true to insert the selected item
        if (event.key === 'Enter') {
          return true
        }
        if (event.key === 'Tab') {
          this.select(this.hover)
          return true
        }
      }
    },
    _select(collaborator) {
      this.command({
        id: collaborator.user_id,
        label: collaborator.name,
      })
    },
    select(collaboratorUserId) {
      const collaborator = this.collaborators.find(
        (c) => c.user_id === collaboratorUserId
      )

      if (collaborator) {
        this._select(collaborator)
      }
    },
  },
}
</script>
