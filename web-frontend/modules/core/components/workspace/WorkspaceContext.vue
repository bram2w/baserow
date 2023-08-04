<template>
  <Context
    ref="context"
    :overflow-scroll="true"
    :max-height-if-outside-viewport="true"
    @shown="fetchRolesAndPermissions"
  >
    <div class="context__menu-title">
      {{ workspace.name }} ({{ workspace.id }})
    </div>
    <div
      v-if="workspace._.additionalLoading"
      class="loading margin-left-2 margin-top-2 margin-bottom-2 margin-bottom-2"
    ></div>
    <ul v-else class="context__menu">
      <li v-if="$hasPermission('workspace.update', workspace, workspace.id)">
        <a @click="$emit('rename')">
          <i class="context__menu-icon fas fa-fw fa-pen"></i>
          {{ $t('workspaceContext.renameWorkspace') }}
        </a>
      </li>
      <li v-if="$hasPermission('invitation.read', workspace, workspace.id)">
        <a
          @click="
            $router.push({
              name: 'settings-members',
              params: {
                workspaceId: workspace.id,
              },
            })
            hide()
          "
        >
          <i class="context__menu-icon fas fa-fw fa-users"></i>
          {{ $t('workspaceContext.members') }}
        </a>
      </li>
      <li
        v-if="$hasPermission('workspace.read_trash', workspace, workspace.id)"
      >
        <a @click="showWorkspaceTrashModal">
          <i class="context__menu-icon fas fa-fw fa-recycle"></i>
          {{ $t('workspaceContext.viewTrash') }}
        </a>
      </li>
      <li>
        <a @click="$refs.leaveWorkspaceModal.show()">
          <i class="context__menu-icon fas fa-fw fa-door-open"></i>
          {{ $t('workspaceContext.leaveWorkspace') }}
        </a>
      </li>
      <li v-if="$hasPermission('workspace.delete', workspace, workspace.id)">
        <a
          :class="{ 'context__menu-item--loading': loading }"
          @click="deleteWorkspace"
        >
          <i class="context__menu-icon fas fa-fw fa-trash"></i>
          {{ $t('workspaceContext.deleteWorkspace') }}
        </a>
      </li>
    </ul>
    <TrashModal
      v-if="$hasPermission('workspace.read_trash', workspace, workspace.id)"
      ref="workspaceTrashModal"
      :initial-workspace="workspace"
    >
    </TrashModal>
    <LeaveWorkspaceModal
      ref="leaveWorkspaceModal"
      :workspace="workspace"
    ></LeaveWorkspaceModal>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import { notifyIf } from '@baserow/modules/core/utils/error'
import TrashModal from '@baserow/modules/core/components/trash/TrashModal'
import LeaveWorkspaceModal from '@baserow/modules/core/components/workspace/LeaveWorkspaceModal'

export default {
  name: 'WorkspaceContext',
  components: { LeaveWorkspaceModal, TrashModal },
  mixins: [context],
  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    async fetchRolesAndPermissions() {
      await this.$store.dispatch('workspace/fetchPermissions', this.workspace)
      await this.$store.dispatch('workspace/fetchRoles', this.workspace)
    },
    showWorkspaceTrashModal() {
      this.$refs.context.hide()
      this.$refs.workspaceTrashModal.show()
    },
    async deleteWorkspace() {
      this.loading = true

      try {
        await this.$store.dispatch('workspace/delete', this.workspace)
        await this.$store.dispatch('toast/restore', {
          trash_item_type: 'workspace',
          trash_item_id: this.workspace.id,
        })
        this.hide()
      } catch (error) {
        notifyIf(error, 'application')
      }

      this.loading = false
    },
  },
}
</script>
