<template>
  <li
    class="agent-conversation-list__item"
    :class="{ 'agent-conversation-list__item--active': active }"
    @click="select"
  >
    <span class="agent-conversation-list__item-origin" :title="origin.label">
      <span
        v-if="loading"
        class="agent-conversation-list__item-origin-loading"
      ></span>
      <img
        v-else-if="origin.image"
        class="agent-conversation-list__item-origin-image"
        :src="origin.image"
        alt=""
      />
      <i v-else :class="origin.icon"></i>
      <span
        v-if="statusModifier"
        class="agent-conversation-list__item-status"
        :class="statusModifier"
        :title="statusTitle"
      ></span>
    </span>
    <span class="agent-conversation-list__item-text">
      <span class="agent-conversation-list__item-heading">
        <span class="agent-conversation-list__item-title">
          <Editable
            ref="rename"
            :value="chat.title || $t('agentConversationList.untitled')"
            @change="renameChat($event)"
          ></Editable>
        </span>
        <span
          v-if="chat.private"
          class="agent-conversation-list__item-private"
          :title="$t('agentConversationList.privateDescription')"
        >
          <i class="iconoir-lock"></i>
          {{ $t('agentConversationList.private') }}
        </span>
      </span>
      <span class="agent-conversation-list__item-meta">
        <span class="agent-conversation-list__item-meta-origin">{{
          origin.label
        }}</span>
        <span
          class="agent-conversation-list__item-meta-time"
          :title="absoluteTime"
          >{{ relativeTime }}</span
        >
      </span>
    </span>
    <a
      v-if="canOpenMenu"
      ref="menuButton"
      class="agent-conversation-list__item-menu"
      :title="$t('agentConversationList.menu')"
      @click="$refs.context.toggle($refs.menuButton, 'bottom', 'right', 4)"
    >
      <i class="iconoir-more-vert"></i>
    </a>
    <AgentConversationContext
      ref="context"
      :application="application"
      :chat="chat"
      @rename="$refs.rename.edit()"
    />
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import AgentConversationContext from '@baserow_enterprise/components/agentApplication/AgentConversationContext'
import { AgentContextMixin } from '@baserow_enterprise/composables/useAgentContext'
import { isChatRunning } from '@baserow_enterprise/utils/agentChatStatus'
import {
  describeChatOrigin,
  getChatOrigin,
} from '@baserow_enterprise/utils/agentChatOrigin'
import moment from '@baserow/modules/core/moment'

export default {
  name: 'AgentConversationListItem',
  mixins: [AgentContextMixin],
  components: { AgentConversationContext },
  props: {
    application: {
      type: Object,
      required: true,
    },
    chat: {
      type: Object,
      required: true,
    },
    active: {
      type: Boolean,
      required: false,
      default: false,
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['select'],
  computed: {
    canOpenMenu() {
      return ['update_chat', 'delete_chat'].some((operation) =>
        this.hasAgentPermission(
          `agent_application.${operation}`,
          this.application,
          this.application.workspace.id
        )
      )
    },
    origin() {
      return describeChatOrigin(getChatOrigin(this.chat), {
        registry: this.$registry,
        t: this.$t.bind(this),
      })
    },
    relativeTime() {
      return moment(this.chat.updated_on).fromNow()
    },
    absoluteTime() {
      return moment(this.chat.updated_on).format('LLL')
    },
    // Idle conversations carry no badge; only what needs attention does.
    statusModifier() {
      if (isChatRunning(this.chat.status)) {
        return 'agent-conversation-list__item-status--running'
      }
      if (['awaiting_approval', 'error'].includes(this.chat.status)) {
        return `agent-conversation-list__item-status--${this.chat.status.replace(
          '_',
          '-'
        )}`
      }
      return null
    },
    statusTitle() {
      if (this.chat.status === 'awaiting_approval') {
        return this.$t('agentConversationList.awaitingApproval')
      }
      if (isChatRunning(this.chat.status)) {
        return this.$t('agentConversationList.running')
      }
      if (this.chat.status === 'error') {
        return this.$t('agentConversationList.failed')
      }
      return null
    },
  },
  methods: {
    // The menu button's click must keep bubbling to the document, where open
    // context menus listen to close themselves, so the row skips it instead
    // of the button stopping it.
    select(event) {
      if (this.$refs.menuButton?.contains(event.target)) {
        return
      }
      this.$emit('select')
    },
    async renameChat({ value }) {
      const title = value.trim()
      if (title === '' || title === this.chat.title) {
        this.$refs.rename.set(this.chat.title || '')
        return
      }
      try {
        await this.$store.dispatch(
          `${this.storePrefix}agentHistory/updateChat`,
          {
            chatUuid: this.chat.uuid,
            values: { title },
          }
        )
      } catch (error) {
        this.$refs.rename.set(this.chat.title || '')
        notifyIf(error, 'application')
      }
    },
  },
}
</script>
