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
  data() {
    return {
      collaborators: [],
      query: '',
      command: () => {},
    }
  },
  computed: {
    isNotFound() {
      return this.results.length === 0
    },
    notFoundErrorMessage() {
      return this.$i18n.t('richTextEditorMentionsList.notFound')
    },
  },
  watch: {
    query(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.fetch(1, this.query).then(() => {
          this.hoverFirstItem()
        })
      }
    },
  },
  mounted() {
    this.$nextTick(() => {
      this.hoverFirstItem()
    })
  },
  methods: {
    hoverFirstItem() {
      this.hover = this.collaborators[0]?.user_id
    },
    filterItems(query) {
      const workspace = this.$store.getters['workspace/getSelected']
      this.collaborators = workspace.users.filter(
        (user) =>
          user.name.toLowerCase().includes(query.toLowerCase()) &&
          user.to_be_deleted === false
      )
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
