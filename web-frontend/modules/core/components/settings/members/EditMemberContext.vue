<template>
  <Context>
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
            $hasPermission('workspace_user.delete', member, group.id)
          "
        >
          <a class="color-error" @click.prevent="showRemoveModal">
            <i class="context__menu-icon fas fa-fw fa-trash"></i>
            {{ $t('membersSettings.membersTable.actions.remove') }}
          </a>
        </li>
      </ul>
    </template>
    <RemoveFromGroupModal
      ref="removeFromGroupModal"
      :group="group"
      :member="member"
      @remove-user="$emit('remove-user', $event)"
    ></RemoveFromGroupModal>
  </Context>
</template>

<script>
import { mapGetters } from 'vuex'

import context from '@baserow/modules/core/mixins/context'
import RemoveFromGroupModal from '@baserow/modules/core/components/group/RemoveFromGroupModal'

export default {
  name: 'EditMemberContext',
  components: {
    RemoveFromGroupModal,
  },
  mixins: [context],
  props: {
    group: {
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
      this.$refs.removeFromGroupModal.show()
    },
    async copyEmail({ email }) {
      await navigator.clipboard.writeText(email)
      this.$refs.emailCopied.show()
    },
  },
}
</script>
