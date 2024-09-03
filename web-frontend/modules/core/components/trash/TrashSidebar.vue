<template>
  <div>
    <div class="modal-sidebar__head">
      <div class="modal-sidebar__head-icon-and-name">
        <i class="modal-sidebar__head-icon-and-name-icon iconoir-bin"></i>
        {{ $t('trashSidebar.title') }}
      </div>
    </div>
    <ul class="trash-sidebar__workspaces">
      <li
        v-for="workspace in workspaces"
        :key="'trash-workspace-' + workspace.id"
        class="trash-sidebar__workspace"
        :class="{
          'trash-sidebar__workspace--active':
            isSelectedTrashWorkspace(workspace),
          'trash-sidebar__workspace--open':
            isSelectedTrashWorkspaceApplication(workspace),
          'trash-sidebar__workspace--trashed': workspace.trashed,
        }"
      >
        <a
          class="trash-sidebar__workspace-link"
          @click="emitIfNotAlreadySelectedTrashWorkspace(workspace)"
        >
          <i
            class="trash-sidebar__workspace-link-caret-right iconoir-nav-arrow-right"
          ></i>
          <i
            class="trash-sidebar__workspace-link-caret-down iconoir-nav-arrow-down"
          ></i>
          {{
            workspace.name ||
            $t('trashSidebar.unnamedWorkspace', { id: workspace.id })
          }}
        </a>
        <ul class="trash-sidebar__applications">
          <li
            v-for="application in workspace.applications"
            :key="'trash-application-' + application.id"
            class="trash-sidebar__application"
            :class="{
              'trash-sidebar__application--active': isSelectedApp(application),
              'trash-sidebar__application--trashed':
                workspace.trashed || application.trashed,
            }"
          >
            <a
              class="trash-sidebar__application-link"
              @click="
                emitIfNotAlreadySelectedTrashApplication(workspace, application)
              "
              >{{
                application.name || 'Unnamed application ' + application.id
              }}</a
            >
          </li>
        </ul>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'TrashSidebar',
  props: {
    workspaces: {
      type: Array,
      required: true,
    },
    selectedTrashWorkspace: {
      type: Object,
      required: false,
      default: null,
    },
    selectedTrashApplication: {
      type: Object,
      required: false,
      default: null,
    },
  },
  methods: {
    isSelectedTrashWorkspace(workspace) {
      return (
        workspace.id === this.selectedTrashWorkspace.id &&
        this.selectedTrashApplication === null
      )
    },
    isSelectedTrashWorkspaceApplication(workspace) {
      return workspace.applications.some((application) =>
        this.isSelectedApp(application)
      )
    },
    isSelectedApp(app) {
      return (
        this.selectedTrashApplication !== null &&
        app.id === this.selectedTrashApplication.id
      )
    },
    emitIfNotAlreadySelectedTrashWorkspace(workspace) {
      if (!this.isSelectedTrashWorkspace(workspace)) {
        this.emitSelected({ workspace })
      }
    },
    emitIfNotAlreadySelectedTrashApplication(workspace, application) {
      if (!this.isSelectedApp(application)) {
        this.emitSelected({ workspace, application })
      }
    },
    emitSelected(selected) {
      this.$emit('selected', selected)
    },
  },
}
</script>
