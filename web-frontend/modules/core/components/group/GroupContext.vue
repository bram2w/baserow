<template>
  <Context ref="context">
    <div class="context__menu-title">{{ group.name }} ({{ group.id }})</div>
    <ul class="context__menu">
      <li v-if="group.permissions === 'ADMIN'">
        <a @click="$emit('rename')">
          <i class="context__menu-icon fas fa-fw fa-pen"></i>
          Rename group
        </a>
      </li>
      <li v-if="group.permissions === 'ADMIN'">
        <a @click=";[$refs.groupMembersModal.show(), hide()]">
          <i class="context__menu-icon fas fa-fw fa-users"></i>
          Members
        </a>
      </li>
      <li v-if="group.permissions === 'ADMIN'">
        <a @click="showGroupTrashModal">
          <i class="context__menu-icon fas fa-fw fa-recycle"></i>
          View trash
        </a>
      </li>
      <li>
        <a @click="$refs.leaveGroupModal.show()">
          <i class="context__menu-icon fas fa-fw fa-door-open"></i>
          Leave group
        </a>
      </li>
      <li v-if="group.permissions === 'ADMIN'">
        <a
          :class="{ 'context__menu-item--loading': loading }"
          @click="deleteGroup"
        >
          <i class="context__menu-icon fas fa-fw fa-trash"></i>
          Delete group
        </a>
      </li>
    </ul>
    <GroupMembersModal
      v-if="group.permissions === 'ADMIN'"
      ref="groupMembersModal"
      :group="group"
    ></GroupMembersModal>
    <TrashModal
      v-if="group.permissions === 'ADMIN'"
      ref="groupTrashModal"
      :initial-group="group"
    >
    </TrashModal>
    <LeaveGroupModal ref="leaveGroupModal" :group="group"></LeaveGroupModal>
  </Context>
</template>

<script>
import GroupMembersModal from '@baserow/modules/core/components/group/GroupMembersModal'
import context from '@baserow/modules/core/mixins/context'
import { notifyIf } from '@baserow/modules/core/utils/error'
import TrashModal from '@baserow/modules/core/components/trash/TrashModal'
import LeaveGroupModal from '@baserow/modules/core/components/group/LeaveGroupModal'

export default {
  name: 'GroupContext',
  components: { LeaveGroupModal, TrashModal, GroupMembersModal },
  mixins: [context],
  props: {
    group: {
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
    showGroupMembersModal() {
      this.$refs.groupMembersModal.show()
    },
    showGroupTrashModal() {
      this.$refs.context.hide()
      this.$refs.groupTrashModal.show()
    },
    async deleteGroup() {
      this.loading = true

      try {
        await this.$store.dispatch('group/delete', this.group)
        await this.$store.dispatch('notification/restore', {
          trash_item_type: 'group',
          trash_item_id: this.group.id,
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
