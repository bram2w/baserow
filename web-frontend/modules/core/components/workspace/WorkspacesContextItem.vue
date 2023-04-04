<template>
  <li
    class="select__item"
    :class="{
      active: workspace._.selected,
      'select__item--loading':
        workspace._.loading || workspace._.additionalLoading,
    }"
  >
    <a class="select__item-link" @click="selectWorkspace(workspace)">
      <div class="select__item-name">
        <Editable
          ref="rename"
          :value="workspace.name"
          @change="renameWorkspace(workspace, $event)"
        ></Editable>
      </div>
    </a>
    <a
      ref="contextLink"
      class="select__item-options"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
      @mousedown.stop
    >
      <i class="fas fa-ellipsis-v"></i>
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
}
</script>
