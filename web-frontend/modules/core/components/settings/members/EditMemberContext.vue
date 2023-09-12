<template>
  <Context :overflow-scroll="true" :max-height-if-outside-viewport="true">
    <template v-if="Object.keys(member).length > 0">
      <ul class="context__menu">
        <li>
          <a @click.prevent="copyEmail(member)">
            <Copied ref="emailCopied"></Copied>
            {{ $t('membersSettings.membersTable.actions.copyEmail') }}
          </a>
        </li>
        <li
          v-if="
            member.user_id !== userId &&
            $hasPermission('workspace_user.delete', member, workspace.id)
          "
        >
          <a class="color-error" @click.prevent="showRemoveModal">
            <i class="context__menu-icon fas fa-fw fa-trash"></i>
            {{ $t('membersSettings.membersTable.actions.remove') }}
          </a>
        </li>
      </ul>
    </template>
    <RemoveFromWorkspaceModal
      ref="removeFromWorkspaceModal"
      :workspace="workspace"
      :member="member"
      @remove-user="$emit('remove-user', $event)"
    ></RemoveFromWorkspaceModal>
  </Context>
</template>

<script>
import { mapGetters } from 'vuex'

import context from '@baserow/modules/core/mixins/context'
import RemoveFromWorkspaceModal from '@baserow/modules/core/components/workspace/RemoveFromWorkspaceModal'

export default {
  name: 'EditMemberContext',
  components: {
    RemoveFromWorkspaceModal,
  },
  mixins: [context],
  props: {
    workspace: {
      required: true,
      type: Object,
    },
    member: {
      required: true,
      type: Object,
    },
  },
  computed: {
    ...mapGetters({
      userId: 'auth/getUserId',
    }),
  },
  methods: {
    showRemoveModal() {
      this.hide()
      this.$refs.removeFromWorkspaceModal.show()
    },
    async copyEmail({ email }) {
      await navigator.clipboard.writeText(email)
      this.$refs.emailCopied.show()
    },
  },
}
</script>
