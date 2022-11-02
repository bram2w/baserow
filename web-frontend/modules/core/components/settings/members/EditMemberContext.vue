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
            $hasPermission('group_user.delete', member, group.id)
          "
        >
          <a
            :class="{
              'context__menu-item--loading': removeLoading,
            }"
            class="color-error"
            @click.prevent="remove(member)"
          >
            <i class="context__menu-icon fas fa-fw fa-trash"></i>
            {{ $t('membersSettings.membersTable.actions.remove') }}
          </a>
        </li>
      </ul>
    </template>
  </Context>
</template>

<script>
import { mapGetters } from 'vuex'

import context from '@baserow/modules/core/mixins/context'
import { notifyIf } from '@baserow/modules/core/utils/error'
import GroupService from '@baserow/modules/core/services/group'

export default {
  name: 'EditMemberContext',
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
  data() {
    return {
      removeLoading: false,
    }
  },
  computed: {
    ...mapGetters({
      userId: 'auth/getUserId',
    }),
  },
  methods: {
    async copyEmail({ email }) {
      await navigator.clipboard.writeText(email)
      this.$refs.emailCopied.show()
    },
    async remove(user) {
      if (this.removeLoading) {
        return
      }

      this.removeLoading = true

      try {
        await GroupService(this.$client).deleteUser(user.id)
        await this.$store.dispatch('group/forceDeleteGroupUser', {
          groupId: this.group.id,
          id: user.id,
          values: { user_id: this.userId },
        })
        this.$emit('refresh')
        this.hide()
      } catch (error) {
        notifyIf(error)
      } finally {
        this.removeLoading = false
      }
    },
  },
}
</script>
