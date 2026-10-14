<template>
  <Context ref="context" :hide-on-click-outside="true">
    <ul class="context__menu">
      <li v-if="canUpdate" class="context__menu-item">
        <a class="context__menu-item-link" @click="togglePinned()">
          <i class="context__menu-item-icon iconoir-pin"></i>
          {{
            chat.pinned
              ? $t('agentConversationList.unpin')
              : $t('agentConversationList.pin')
          }}
        </a>
      </li>
      <li v-if="canUpdate" class="context__menu-item">
        <a class="context__menu-item-link" @click="rename()">
          <i class="context__menu-item-icon iconoir-edit-pencil"></i>
          {{ $t('agentConversationList.rename') }}
        </a>
      </li>
      <li v-if="canChangePrivacy" class="context__menu-item">
        <a class="context__menu-item-link" @click="togglePrivate()">
          <i
            class="context__menu-item-icon"
            :class="chat.private ? 'iconoir-community' : 'iconoir-lock'"
          ></i>
          {{
            chat.private
              ? $t('agentConversationList.makePublic')
              : $t('agentConversationList.makePrivate')
          }}
        </a>
      </li>
      <li v-if="canDelete" class="context__menu-item">
        <a
          class="context__menu-item-link context__menu-item-link--delete"
          :class="{ 'context__menu-item-link--loading': deleting }"
          @click="deleteChat()"
        >
          <i class="context__menu-item-icon iconoir-bin"></i>
          {{ $t('agentConversationList.delete') }}
        </a>
      </li>
      <li
        v-if="usageLine"
        class="context__menu-item context__menu-item--with-separator"
      >
        <div
          class="agent-conversation-context__usage"
          :title="
            $t('agentUsage.conversationBreakdown', {
              input: (chat.total_input_tokens || 0).toLocaleString(),
              output: (chat.total_output_tokens || 0).toLocaleString(),
            })
          "
        >
          {{ usageLine }}
        </div>
      </li>
    </ul>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { AgentContextMixin } from '@baserow_enterprise/composables/useAgentContext'
import { isChatRunning } from '@baserow_enterprise/utils/agentChatStatus'
import {
  formatCost,
  formatTokens,
  hasCost,
  totalTokens,
} from '@baserow_enterprise/utils/agentUsage'

export default {
  name: 'AgentConversationContext',
  mixins: [AgentContextMixin, context],
  props: {
    application: {
      type: Object,
      required: true,
    },
    chat: {
      type: Object,
      required: true,
    },
  },
  emits: ['rename'],
  data() {
    return { deleting: false }
  },
  computed: {
    usageLine() {
      const tokens = totalTokens(this.chat)
      if (tokens === 0) {
        return ''
      }
      return hasCost(this.chat)
        ? this.$t('agentUsage.conversation', {
            tokens: formatTokens(tokens),
            cost: formatCost(this.chat.total_cost),
          })
        : this.$t('agentUsage.conversationTokens', {
            tokens: formatTokens(tokens),
          })
    },
    canUpdate() {
      return this.hasAgentPermission(
        'agent_application.update_chat',
        this.application,
        this.application.workspace.id
      )
    },
    // Only the person who started a conversation decides who sees it.
    canChangePrivacy() {
      return (
        this.canUpdate &&
        ['manual', 'setup'].includes(this.chat.source) &&
        this.chat.user_id !== null &&
        this.chat.user_id === this.$store.getters['auth/getUserId']
      )
    },
    canDelete() {
      return (
        !isChatRunning(this.chat.status) &&
        this.hasAgentPermission(
          'agent_application.delete_chat',
          this.application,
          this.application.workspace.id
        )
      )
    },
  },
  methods: {
    async togglePinned() {
      this.hide()
      try {
        await this.$store.dispatch(
          `${this.storePrefix}agentHistory/updateChat`,
          {
            chatUuid: this.chat.uuid,
            values: { pinned: !this.chat.pinned },
          }
        )
      } catch (error) {
        notifyIf(error, 'application')
      }
    },
    async togglePrivate() {
      this.hide()
      const values = { private: !this.chat.private }
      try {
        if (
          this.$store.getters[`${this.storePrefix}agentChat/getChatId`] ===
          this.chat.id
        ) {
          // The open conversation shows its state in the composer too.
          await this.$store.dispatch(
            `${this.storePrefix}agentChat/setPrivate`,
            values
          )
        } else {
          await this.$store.dispatch(
            `${this.storePrefix}agentHistory/updateChat`,
            { chatUuid: this.chat.uuid, values }
          )
        }
      } catch (error) {
        notifyIf(error, 'application')
      }
    },
    rename() {
      this.hide()
      this.$emit('rename')
    },
    async deleteChat() {
      if (this.deleting) {
        return
      }
      this.deleting = true
      try {
        await this.$store.dispatch(
          `${this.storePrefix}agentHistory/deleteChat`,
          {
            chat: this.chat,
          }
        )
        // The deleted conversation's row, this menu included, may already be
        // gone.
        if (this.$refs.context) {
          this.hide()
        }
      } catch (error) {
        notifyIf(error, 'application')
      } finally {
        this.deleting = false
      }
    },
  },
}
</script>
