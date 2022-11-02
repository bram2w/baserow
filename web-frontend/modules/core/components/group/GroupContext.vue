<template>
  <Context ref="context" @shown="fetchRolesAndPermissions">
    <div class="context__menu-title">{{ group.name }} ({{ group.id }})</div>
    <div
      v-if="group._.additionalLoading"
      class="loading margin-left-2 margin-top-2 margin-bottom-2 margin-bottom-2"
    ></div>
    <ul v-else class="context__menu">
      <li v-if="$hasPermission('group.update', group, group.id)">
        <a @click="$emit('rename')">
          <i class="context__menu-icon fas fa-fw fa-pen"></i>
          {{ $t('groupContext.renameGroup') }}
        </a>
      </li>
      <li v-if="$hasPermission('invitation.read', group, group.id)">
        <a
          @click="
            $router.push({
              name: 'settings-members',
              params: {
                groupId: group.id,
              },
            })
            hide()
          "
        >
          <i class="context__menu-icon fas fa-fw fa-users"></i>
          {{ $t('groupContext.members') }}
        </a>
      </li>
      <li v-if="$hasPermission('group.read_trash', group, group.id)">
        <a @click="showGroupTrashModal">
          <i class="context__menu-icon fas fa-fw fa-recycle"></i>
          {{ $t('groupContext.viewTrash') }}
        </a>
      </li>
      <li>
        <a @click="$refs.leaveGroupModal.show()">
          <i class="context__menu-icon fas fa-fw fa-door-open"></i>
          {{ $t('groupContext.leaveGroup') }}
        </a>
      </li>
      <li v-if="$hasPermission('group.delete', group, group.id)">
        <a
          :class="{ 'context__menu-item--loading': loading }"
          @click="deleteGroup"
        >
          <i class="context__menu-icon fas fa-fw fa-trash"></i>
          {{ $t('groupContext.deleteGroup') }}
        </a>
      </li>
    </ul>
    <TrashModal
      v-if="$hasPermission('group.read_trash', group, group.id)"
      ref="groupTrashModal"
      :initial-group="group"
    >
    </TrashModal>
    <LeaveGroupModal ref="leaveGroupModal" :group="group"></LeaveGroupModal>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import { notifyIf } from '@baserow/modules/core/utils/error'
import TrashModal from '@baserow/modules/core/components/trash/TrashModal'
import LeaveGroupModal from '@baserow/modules/core/components/group/LeaveGroupModal'

export default {
  name: 'GroupContext',
  components: { LeaveGroupModal, TrashModal },
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
    async fetchRolesAndPermissions() {
      await this.$store.dispatch('group/fetchPermissions', this.group)
      await this.$store.dispatch('group/fetchRoles', this.group)
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
