<template>
  <Context ref="context">
    <div class="context__menu-title">{{ group.name }} ({{ group.id }})</div>
    <ul class="context__menu">
      <li v-if="group.permissions === 'ADMIN'">
        <a @click="$emit('rename')">
          <i class="context__menu-icon fas fa-fw fa-pen"></i>
          {{ $t('groupContext.renameGroup') }}
        </a>
      </li>
      <li v-if="group.permissions === 'ADMIN'">
        <a @click=";[$refs.groupMembersModal.show(), hide()]">
          <i class="context__menu-icon fas fa-fw fa-users"></i>
          {{ $t('groupContext.members') }}
        </a>
      </li>
      <li v-if="group.permissions === 'ADMIN'">
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
      <li v-if="group.permissions === 'ADMIN'">
        <a
          :class="{ 'context__menu-item--loading': loading }"
          @click="deleteGroup"
        >
          <i class="context__menu-icon fas fa-fw fa-trash"></i>
          {{ $t('groupContext.deleteGroup') }}
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
      // We need to make sure that the group members modal is rendered before we can
      // open it.
      this.$refs.context.forceRender()
      this.$nextTick(() => {
        this.$refs.groupMembersModal.show()
      })
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

<i18n>
{
  "en": {
    "groupContext": {
      "renameGroup": "Rename group",
      "members": "Members",
      "viewTrash": "View trash",
      "leaveGroup": "Leave group",
      "deleteGroup": "Delete group"
    }
  },
  "fr": {
    "groupContext": {
      "renameGroup": "Renommer le groupe",
      "members": "Membres",
      "viewTrash": "Voir la corbeille",
      "leaveGroup": "Quitter le groupe",
      "deleteGroup": "Supprimer le groupe"
    }
  }
}
</i18n>
