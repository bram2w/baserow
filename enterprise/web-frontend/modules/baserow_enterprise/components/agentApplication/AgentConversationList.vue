<template>
  <div class="agent-conversation-list">
    <div class="agent-conversation-list__scroll">
      <Dropdown
        v-if="!pageLoading"
        class="agent-conversation-list__filter"
        :model-value="origin"
        :show-search="false"
        @update:model-value="setOrigin"
      >
        <DropdownItem
          :name="$t('agentConversationList.allConversations')"
          :value="null"
          icon="iconoir-filter-list"
        />
        <DropdownItem
          v-for="option in originOptions"
          :key="option.value"
          :name="option.label"
          :value="option.value"
          :icon="option.image ? '' : option.icon"
          :image="option.image"
        />
      </Dropdown>
      <!-- A new filter shows placeholders until its conversations arrive. -->
      <template v-if="pageLoading || filtering">
        <div class="agent-conversation-list__section-title">
          {{ $t('agentConversationList.recent') }}
        </div>
        <ul class="agent-conversation-list__items">
          <li
            v-for="index in 8"
            :key="index"
            class="agent-conversation-list__item agent-conversation-list__item--skeleton"
          >
            <SkeletonBlock width="28px" height="28px" />
            <span class="agent-conversation-list__item-text">
              <SkeletonBlock
                :width="`${skeletonWidths[index % skeletonWidths.length]}%`"
                height="12px"
              />
              <SkeletonBlock width="40%" height="8px" />
            </span>
          </li>
        </ul>
      </template>
      <template v-else>
        <template v-if="pinnedChats.length > 0">
          <div class="agent-conversation-list__section-title">
            {{ $t('agentConversationList.pinned') }}
          </div>
          <ul class="agent-conversation-list__items">
            <AgentConversationListItem
              v-for="chat in pinnedChats"
              :key="chat.id"
              :application="application"
              :chat="chat"
              :active="isCurrent(chat)"
              :loading="isLoading(chat)"
              @select="selectChat(chat)"
            />
          </ul>
        </template>
        <div class="agent-conversation-list__section-title">
          {{ $t('agentConversationList.recent') }}
        </div>
        <div
          v-if="recentChats.length === 0"
          class="agent-conversation-list__empty"
        >
          {{
            origin === null
              ? $t('agentConversationList.empty')
              : $t('agentConversationList.emptyFiltered')
          }}
        </div>
        <ul v-else class="agent-conversation-list__items">
          <AgentConversationListItem
            v-for="chat in recentChats"
            :key="chat.id"
            :application="application"
            :chat="chat"
            :active="isCurrent(chat)"
            :loading="isLoading(chat)"
            @select="selectChat(chat)"
          />
        </ul>
        <ButtonText
          v-if="hasMore"
          class="agent-conversation-list__load-more"
          icon="iconoir-nav-arrow-down"
          :loading="loading"
          @click="loadMore"
        >
          {{ $t('agentConversationList.loadMore') }}
        </ButtonText>
      </template>
    </div>
    <div
      v-if="canStartChat && !pageLoading"
      class="agent-conversation-list__footer"
    >
      <Button
        type="secondary"
        icon="iconoir-plus"
        full-width
        @click="newConversation(false)"
      >
        {{ $t('agentConversationList.newConversation') }}
      </Button>
      <Button
        v-tooltip="$t('agentConversationList.newPrivateConversation')"
        tooltip-position="top"
        type="secondary"
        icon="iconoir-lock"
        @click="newConversation(true)"
      ></Button>
    </div>
  </div>
</template>

<script>
import { defineComponent, computed, ref } from 'vue'
import { useStore } from 'vuex'
import { useNuxtApp, useI18n } from '#imports'
import { notifyIf } from '@baserow/modules/core/utils/error'
import AgentConversationListItem from '@baserow_enterprise/components/agentApplication/AgentConversationListItem'
import { useAgentContext } from '@baserow_enterprise/composables/useAgentContext'
import {
  describeChatOrigin,
  ORIGIN_MINE,
} from '@baserow_enterprise/utils/agentChatOrigin'

export default defineComponent({
  name: 'AgentConversationList',
  components: { AgentConversationListItem },
  props: {
    // The page is still fetching the agent; the list shows placeholders.
    pageLoading: {
      type: Boolean,
      required: false,
      default: false,
    },
    application: {
      type: Object,
      required: true,
    },
  },
  setup(props) {
    // Varied title lengths so the placeholder reads as a list of titles.
    const skeletonWidths = [70, 45, 60, 80, 50]
    const store = useStore()
    const { storePrefix, hasPermission } = useAgentContext()

    const { $registry } = useNuxtApp()
    const { t } = useI18n()

    const canStartChat = computed(
      () =>
        hasPermission(
          'agent_application.run_chat',
          props.application,
          props.application.workspace.id
        ) &&
        hasPermission(
          'agent_application.start_chat',
          props.application,
          props.application.workspace.id
        )
    )
    const origin = computed(
      () => store.getters[`${storePrefix}agentHistory/getOrigin`]
    )
    // Offered: how conversations can start with the current configuration,
    // plus the active filter if that's no longer one of them.
    const originOptions = computed(() => {
      const values = [ORIGIN_MINE, 'manual']
      for (const trigger of store.getters[
        `${storePrefix}agentApplication/getTriggers`
      ]) {
        const type = String(trigger.service_type || '').replace(
          /^local_baserow_/,
          ''
        )
        values.push(`trigger:${type}`)
      }
      for (const channel of store.getters[
        `${storePrefix}agentApplication/getChannels`
      ]) {
        values.push(`channel:${channel.type}`)
      }
      values.push('service')
      if (origin.value !== null) {
        values.push(origin.value)
      }
      return [...new Set(values)].map((value) => ({
        value,
        ...describeChatOrigin(value, { registry: $registry, t }),
      }))
    })
    const filtering = ref(false)
    let latestOrigin = null
    const setOrigin = async (value) => {
      if (value === origin.value) {
        return
      }
      latestOrigin = value
      filtering.value = true
      try {
        await store.dispatch(`${storePrefix}agentHistory/setOrigin`, {
          applicationId: props.application.id,
          origin: value,
        })
      } catch (error) {
        notifyIf(error, 'application')
      } finally {
        // Picking another filter meanwhile keeps the placeholders until the
        // latest one arrived.
        if (latestOrigin === value) {
          filtering.value = false
        }
      }
    }
    const pinnedChats = computed(
      () => store.getters[`${storePrefix}agentHistory/getPinnedChats`]
    )
    const recentChats = computed(
      () => store.getters[`${storePrefix}agentHistory/getRecentChats`]
    )
    const currentChatUuid = computed(
      () => store.getters[`${storePrefix}agentChat/getCurrentChatUuid`]
    )
    const isCurrent = (chat) => chat.uuid === currentChatUuid.value

    const hasMore = computed(
      () => store.getters[`${storePrefix}agentHistory/hasMore`]
    )
    const loading = computed(
      () => store.getters[`${storePrefix}agentHistory/isLoading`]
    )
    const loadMore = async () => {
      try {
        await store.dispatch(`${storePrefix}agentHistory/fetchMore`, {
          applicationId: props.application.id,
        })
      } catch (error) {
        notifyIf(error, 'application')
      }
    }

    const loadingChatUuid = computed(
      () => store.getters[`${storePrefix}agentChat/getLoadingChatUuid`]
    )
    const isLoading = (chat) => chat.uuid === loadingChatUuid.value
    const selectChat = async (chat) => {
      if (isLoading(chat) || isCurrent(chat)) {
        return
      }
      try {
        await store.dispatch(`${storePrefix}agentChat/openConversation`, {
          applicationId: props.application.id,
          chatUuid: chat.uuid,
        })
      } catch (error) {
        notifyIf(error, 'application')
      }
    }
    const newConversation = (isPrivate) => {
      store.dispatch(`${storePrefix}agentChat/newConversation`, {
        private: isPrivate,
      })
    }

    return {
      skeletonWidths,
      canStartChat,
      origin,
      filtering,
      originOptions,
      setOrigin,
      pinnedChats,
      recentChats,
      hasMore,
      loading,
      isLoading,
      isCurrent,
      selectChat,
      newConversation,
      loadMore,
    }
  },
})
</script>
