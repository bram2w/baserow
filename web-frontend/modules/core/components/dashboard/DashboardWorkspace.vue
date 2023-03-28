<template>
  <div class="dashboard__group">
    <div class="dashboard__group-head">
      <div
        class="dashboard__group-title"
        :class="{ 'dashboard__group-title--loading': workspace._.loading }"
      >
        <Editable
          ref="rename"
          :value="workspace.name"
          @change="renameWorkspace(workspace, $event)"
        ></Editable>
        <a
          ref="contextLink"
          class="dashboard__group-title-options"
          @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
        >
          <i class="dashboard__group-title-icon fas fa-caret-down"></i>
        </a>
      </div>
      <WorkspaceContext
        ref="context"
        :workspace="workspace"
        @rename="enableRename()"
      ></WorkspaceContext>
      <div class="dashboard__group-title-extra">
        <component
          :is="component"
          v-for="(component, index) in dashboardWorkspaceExtraComponents"
          :key="index"
          :workspace="workspace"
          :component-arguments="componentArguments"
        ></component>
      </div>
    </div>
    <component
      :is="component"
      v-for="(component, index) in dashboardWorkspaceComponents"
      :key="index"
      :workspace="workspace"
      :component-arguments="componentArguments"
    ></component>
    <ul class="dashboard__group-items">
      <li
        v-for="application in getAllOfWorkspace(workspace)"
        :key="application.id"
        class="dashboard__group-item"
      >
        <a
          class="dashboard__group-item-link"
          @click="selectApplication(application)"
        >
          <div class="dashboard__group-item-icon">
            <i class="fas" :class="'fa-' + application._.type.iconClass"></i>
          </div>
          <div class="dashboard__group-item-name">
            {{ application.name }}
          </div>
        </a>
      </li>
      <li class="dashboard__group-item">
        <a
          ref="createApplicationContextLink"
          class="dashboard__group-item-link"
          @click="
            $refs.createApplicationContext.toggle(
              $refs.createApplicationContextLink
            )
          "
        >
          <div
            class="dashboard__group-item-icon dashboard__group-item-icon--add"
          >
            <i class="fas fa-plus"></i>
          </div>

          <div class="dashboard__group-item-name">
            {{ $t('dashboardWorkspace.createApplication') }}
          </div>
        </a>
        <CreateApplicationContext
          ref="createApplicationContext"
          :workspace="workspace"
        ></CreateApplicationContext>
      </li>
    </ul>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import CreateApplicationContext from '@baserow/modules/core/components/application/CreateApplicationContext'
import WorkspaceContext from '@baserow/modules/core/components/workspace/WorkspaceContext'
import editWorkspace from '@baserow/modules/core/mixins/editWorkspace'

export default {
  components: {
    CreateApplicationContext,
    WorkspaceContext,
  },
  mixins: [editWorkspace],
  props: {
    workspace: {
      type: Object,
      required: true,
    },
    componentArguments: {
      type: Object,
      required: true,
    },
  },
  computed: {
    dashboardWorkspaceExtraComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getDashboardWorkspaceExtraComponent())
        .filter((component) => component !== null)
    },
    dashboardWorkspaceComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getDashboardWorkspaceComponent())
        .filter((component) => component !== null)
    },
    ...mapGetters({
      getAllOfWorkspace: 'application/getAllOfWorkspace',
    }),
  },
  methods: {
    selectApplication(application) {
      const type = this.$registry.get('application', application.type)
      type.select(application, this)
    },
  },
}
</script>
