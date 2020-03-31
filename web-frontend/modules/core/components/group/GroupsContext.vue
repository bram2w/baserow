<template>
  <Context ref="groupsContext" class="select">
    <div class="select-search">
      <i class="select-search-icon fas fa-search"></i>
      <input
        v-model="query"
        type="text"
        class="select-search-input"
        placeholder="Search views"
      />
    </div>
    <div v-if="isLoading" class="context-loading">
      <div class="loading"></div>
    </div>
    <ul v-if="!isLoading && isLoaded && groups.length > 0" class="select-items">
      <GroupsContextItem
        v-for="group in searchAndSort(groups)"
        :key="group.id"
        :group="group"
        @selected="hide"
      ></GroupsContextItem>
    </ul>
    <div
      v-if="!isLoading && isLoaded && groups.length == 0"
      class="context-description"
    >
      No results found
    </div>
    <div class="select-footer">
      <a class="select-footer-button" @click="$refs.createGroupModal.show()">
        <i class="fas fa-plus"></i>
        Create group
      </a>
    </div>
    <CreateGroupModal ref="createGroupModal"></CreateGroupModal>
  </Context>
</template>

<script>
import { mapGetters, mapState } from 'vuex'

import CreateGroupModal from '@baserow/modules/core/components/group/CreateGroupModal'
import GroupsContextItem from '@baserow/modules/core/components/group/GroupsContextItem'
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'GroupsContext',
  components: {
    CreateGroupModal,
    GroupsContextItem,
  },
  mixins: [context],
  data() {
    return {
      query: '',
    }
  },
  computed: {
    ...mapState({
      groups: (state) => state.group.items,
    }),
    ...mapGetters({
      isLoading: 'group/isLoading',
      isLoaded: 'group/isLoaded',
    }),
  },
  methods: {
    /**
     * When the groups context select is opened for the for the first time we must make
     * sure that all the groups are already loaded or going to be loaded.
     */
    toggle(...args) {
      this.$store.dispatch('group/loadAll')
      this.getRootContext().toggle(...args)
    },
    searchAndSort(groups) {
      const query = this.query

      return groups.filter(function (group) {
        const regex = new RegExp('(' + query + ')', 'i')
        return group.name.match(regex)
      })
      // .sort((a, b) => {
      //   return a.order - b.order
      // })
    },
  },
}
</script>
