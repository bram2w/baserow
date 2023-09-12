<template>
  <Context :overflow-scroll="true" :max-height-if-outside-viewport="true">
    <template v-if="Object.keys(workspace).length > 0">
      <div class="context__menu-title">
        {{ workspace.name }} ({{ workspace.id }})
      </div>
      <ul class="context__menu">
        <li>
          <a @click.prevent="showDeleteModal">
            <i class="context__menu-icon fas fa-fw fa-trash-alt"></i>
            {{ $t('editWorkspaceContext.delete') }}
          </a>
        </li>
      </ul>
      <DeleteWorkspaceModal
        ref="deleteWorkspaceModal"
        :workspace="workspace"
        @workspace-deleted="$emit('workspace-deleted', $event)"
      ></DeleteWorkspaceModal>
    </template>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import DeleteWorkspaceModal from '@baserow_premium/components/admin/workspaces/modals/DeleteWorkspaceModal'

export default {
  name: 'EditWorkspaceContext',
  components: { DeleteWorkspaceModal },
  mixins: [context],
  props: {
    workspace: {
      required: true,
      type: Object,
    },
  },
  methods: {
    showDeleteModal() {
      this.hide()
      this.$refs.deleteWorkspaceModal.show()
    },
  },
}
</script>
