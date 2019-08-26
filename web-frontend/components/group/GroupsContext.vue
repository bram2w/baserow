<template>
  <Context class="select">
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
      <li
        v-for="group in searchAndSort(groups)"
        :key="group.id"
        :ref="'groupSelect' + group.id"
        class="select-item"
      >
        <div class="loading-overlay"></div>
        <a class="select-item-link">
          <Editable
            :ref="'groupRename' + group.id"
            :value="group.name"
            @change="renameGroup(group, $event)"
          ></Editable>
        </a>
        <a
          :ref="'groupOptions' + group.id"
          class="select-item-options"
          @click="toggleContext(group.id)"
        >
          <i class="fas fa-ellipsis-v"></i>
        </a>
      </li>
    </ul>
    <div
      v-if="!isLoading && isLoaded && groups.length == 0"
      class="context-description"
    >
      No results found
    </div>
    <Context ref="groupsItemContext">
      <ul class="context-menu">
        <li>
          <a @click="toggleRename(contextId)">
            <i class="context-menu-icon fas fa-fw fa-pen"></i>
            Rename group
          </a>
        </li>
        <li>
          <a @click="deleteGroup(contextId)">
            <i class="context-menu-icon fas fa-fw fa-trash"></i>
            Delete group
          </a>
        </li>
      </ul>
    </Context>
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

import CreateGroupModal from '@/components/group/CreateGroupModal'
import context from '@/mixins/context'

export default {
  name: 'GroupsItemContext',
  components: {
    CreateGroupModal
  },
  mixins: [context],
  data() {
    return {
      query: '',
      contextId: -1
    }
  },
  computed: {
    ...mapState({
      groups: state => state.group.items
    }),
    ...mapGetters({
      isLoading: 'group/isLoading',
      isLoaded: 'group/isLoaded'
    })
  },
  methods: {
    toggle(...args) {
      this.$store.dispatch('group/loadAll')
      this.getRootContext().toggle(...args)
    },
    toggleContext(groupId) {
      const target = this.$refs['groupOptions' + groupId][0]
      this.contextId = groupId
      this.$refs.groupsItemContext.toggle(target, 'bottom', 'right', 0)
    },
    searchAndSort(groups) {
      const query = this.query

      return groups.filter(function(group) {
        const regex = new RegExp('(' + query + ')', 'i')
        return group.name.match(regex)
      })
      // .sort((a, b) => {
      //   return a.order - b.order
      // })
    },
    toggleRename(id) {
      this.$refs.groupsItemContext.hide()
      this.$refs['groupRename' + id][0].edit()
    },
    renameGroup(group, event) {
      const select = this.$refs['groupSelect' + group.id][0]
      select.classList.add('select-item-loading')

      this.$store
        .dispatch('group/update', {
          id: group.id,
          values: {
            name: event.value
          }
        })
        .catch(() => {
          // If something is going wrong we will reset the original value
          const rename = this.$refs['groupRename' + group.id][0]
          rename.set(event.oldValue)
        })
        .then(() => {
          select.classList.remove('select-item-loading')
        })
    },
    deleteGroup(id) {
      this.$refs.groupsItemContext.hide()
      const select = this.$refs['groupSelect' + id][0]
      select.classList.add('select-item-loading')

      this.$store.dispatch('group/delete', id).catch(() => {
        select.classList.remove('select-item-loading')
      })
    }
  }
}
</script>
