<template>
  <li
    class="select__item"
    :class="{
      active: workspace._.selected,
      'select__item--loading':
        workspace._.loading || workspace._.additionalLoading,
      'select__item--has-notification': hasUnreadNotifications,
    }"
  >
    <a class="select__item-link" @click="selectWorkspace(workspace)">
      <div :title="workspace.name" class="select__item-name">
        <span class="select__item-name-text">
          <Editable
            ref="rename"
            :value="workspace.name"
            @change="renameWorkspace(workspace, $event)"
          ></Editable>
        </span>
        <span
          v-if="hasUnreadNotifications"
          class="sidebar__unread-notifications-icon"
        ></span>
      </div>
    </a>
    <i
      v-if="workspace._.selected"
      class="select__item-active-icon iconoir-check"
    ></i>
    <a
      ref="contextLink"
      class="select__item-options"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
      @mousedown.stop
    >
      <i class="baserow-icon-more-vertical"></i>
    </a>
    <WorkspaceContext
      ref="context"
      :workspace="workspace"
      @rename="enableRename()"
    ></WorkspaceContext>
  </li>
</template>

<script>
import WorkspaceContext from '@baserow/modules/core/components/workspace/WorkspaceContext'
import editWorkspace from '@baserow/modules/core/mixins/editWorkspace'

export default {
  name: 'WorkspacesContextItem',
  components: { WorkspaceContext },
  mixins: [editWorkspace],
  props: {
    workspace: {
      type: Object,
      required: true,
    },
  },
  computed: {
    hasUnreadNotifications() {
      return this.$store.getters['notification/workspaceHasUnread'](
        this.workspace.id
      )
    },
  },
}
</script>
