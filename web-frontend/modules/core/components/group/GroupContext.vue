<template>
  <Context ref="context">
    <div class="context__menu-title">{{ group.name }} ({{ group.id }})</div>
    <ul class="context__menu">
      <li>
        <a @click="$emit('rename')">
          <i class="context__menu-icon fas fa-fw fa-pen"></i>
          Rename group
        </a>
      </li>
      <li>
        <a @click=";[$refs.groupMembersModal.show(), hide()]">
          <i class="context__menu-icon fas fa-fw fa-users"></i>
          Members
        </a>
      </li>
      <li>
        <a @click="$refs.deleteGroupModal.show()">
          <i class="context__menu-icon fas fa-fw fa-trash"></i>
          Delete group
        </a>
      </li>
    </ul>
    <GroupMembersModal
      ref="groupMembersModal"
      :group="group"
    ></GroupMembersModal>
    <DeleteGroupModal ref="deleteGroupModal" :group="group" />
  </Context>
</template>

<script>
import DeleteGroupModal from '@baserow/modules/core/components/group/DeleteGroupModal'
import GroupMembersModal from '@baserow/modules/core/components/group/GroupMembersModal'
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'GroupContext',
  components: { DeleteGroupModal, GroupMembersModal },
  mixins: [context],
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  methods: {
    showGroupMembersModal() {
      this.$refs.groupMembersModal.show()
    },
  },
}
</script>
