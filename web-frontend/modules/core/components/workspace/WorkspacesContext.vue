<template>
  <Context
    ref="workspacesContext"
    class="select"
    :max-height-if-outside-viewport="true"
  >
    <div class="select__search">
      <i class="select__search-icon fas fa-search"></i>
      <input
        v-model="query"
        type="text"
        class="select__search-input"
        :placeholder="$t('workspacesContext.search')"
      />
    </div>
    <div v-if="isLoading" class="context--loading">
      <div class="loading"></div>
    </div>
    <ul
      v-if="!isLoading && isLoaded && workspaces.length > 0"
      v-auto-overflow-scroll
      class="select__items select__items--no-max-height"
    >
      <WorkspacesContextItem
        v-for="workspace in searchAndSort(workspaces)"
        :key="workspace.id"
        v-sortable="{ id: workspace.id, update: order, marginTop: -1.5 }"
        :workspace="workspace"
        @selected="hide"
      ></WorkspacesContextItem>
    </ul>
    <div
      v-if="!isLoading && isLoaded && workspaces.length == 0"
      class="context__description"
    >
      {{ $t('workspacesContext.noResults') }}
    </div>
    <div class="select__footer">
      <a
        v-if="$hasPermission('create_workspace')"
        class="select__footer-button"
        @click="$refs.createWorkspaceModal.show()"
      >
        <i class="fas fa-plus"></i>
        {{ $t('workspacesContext.createWorkspace') }}
      </a>
    </div>
    <CreateWorkspaceModal
      ref="createWorkspaceModal"
      @created="hide"
    ></CreateWorkspaceModal>
  </Context>
</template>

<script>
import { mapGetters, mapState } from 'vuex'

import CreateWorkspaceModal from '@baserow/modules/core/components/workspace/CreateWorkspaceModal'
import WorkspacesContextItem from '@baserow/modules/core/components/workspace/WorkspacesContextItem'
import context from '@baserow/modules/core/mixins/context'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { escapeRegExp } from '@baserow/modules/core/utils/string'

export default {
  name: 'WorkspacesContext',
  components: {
    CreateWorkspaceModal,
    WorkspacesContextItem,
  },
  mixins: [context],
  data() {
    return {
      query: '',
    }
  },
  computed: {
    ...mapState({
      workspaces: (state) => state.workspace.items,
    }),
    ...mapGetters({
      isLoading: 'workspace/isLoading',
      isLoaded: 'workspace/isLoaded',
    }),
  },
  methods: {
    /**
     * When the workspaces context select is opened for the first time we must make
     * sure that all the workspaces are already loaded or going to be loaded.
     */
    toggle(...args) {
      this.$store.dispatch('workspace/loadAll')
      this.getRootContext().toggle(...args)
    },
    searchAndSort(workspaces) {
      const query = this.query

      return workspaces
        .filter(function (workspace) {
          const regex = new RegExp('(' + escapeRegExp(query) + ')', 'i')
          return workspace.name.match(regex)
        })
        .sort((a, b) => {
          return a.order - b.order
        })
    },
    async order(order, oldOrder) {
      try {
        await this.$store.dispatch('workspace/order', {
          order,
          oldOrder,
        })
      } catch (error) {
        notifyIf(error, 'workspace')
      }
    },
  },
}
</script>
