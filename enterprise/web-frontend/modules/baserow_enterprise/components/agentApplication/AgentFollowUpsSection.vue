<template>
  <div>
    <div class="agent-configuration__hint margin-bottom-2">
      {{ $t('agentFollowUps.intro') }}
    </div>
    <SegmentControl
      v-model:active-index="filterIndex"
      :segments="filterSegments"
      size="small"
      class="margin-bottom-2"
    />
    <div v-if="loading" class="loading"></div>
    <div
      v-else-if="visible.length === 0"
      class="agent-configuration__placeholder"
    >
      {{ $t(`agentFollowUps.empty_${filters[filterIndex]}`) }}
    </div>
    <div v-else class="agent-configuration__card-list">
      <AgentConfigurationCard
        v-for="followUp in visible"
        :key="followUp.id"
        :default-expanded="false"
        :title="followUp.title || $t('agentFollowUps.privateTitle')"
        :subtitle="subtitle(followUp)"
        :icon="followUp.private ? 'iconoir-lock' : 'iconoir-bell'"
      >
        <div class="agent-follow-up__meta">
          <span>{{
            $t('agentFollowUps.createdBy', {
              name: followUp.created_by?.name || $t('agentFollowUps.someone'),
              time: relative(followUp.created_on),
            })
          }}</span>
          <span v-if="followUp.last_checked_on">{{
            $t('agentFollowUps.lastChecked', {
              time: relative(followUp.last_checked_on),
              count: followUp.checks_count,
            })
          }}</span>
          <span v-else>{{ $t('agentFollowUps.notCheckedYet') }}</span>
          <AgentUsageSummary
            v-if="totalTokens(followUp) > 0"
            :usage="followUp"
          />
        </div>
        <div
          v-if="followUp.outcome"
          class="agent-follow-up__outcome"
          :class="`agent-follow-up__outcome--${followUp.status}`"
        >
          {{ followUp.outcome }}
        </div>
        <AgentKeyValueList
          v-if="!isRedacted(followUp)"
          :fields="followUpFields(followUp, t)"
        />
        <div v-else class="agent-configuration__hint">
          {{ $t('agentFollowUps.privateDescription') }}
        </div>
        <template
          v-if="followUp.source_chat_uuid || canManage(followUp)"
          #footer
        >
          <div class="agent-follow-up__actions">
            <Button
              v-if="canManage(followUp)"
              type="secondary"
              size="small"
              icon="iconoir-refresh"
              :loading="checking === followUp.id"
              :disabled="checking !== null"
              @click="checkNow(followUp)"
            >
              {{ $t('agentFollowUps.checkNow') }}
            </Button>
            <Button
              v-if="followUp.source_chat_uuid"
              type="secondary"
              size="small"
              icon="iconoir-chat-bubble-empty"
              @click="emit('open-conversation', followUp.source_chat_uuid)"
            >
              {{ $t('agentFollowUps.openConversation') }}
            </Button>
            <Button
              v-if="canManage(followUp)"
              type="secondary"
              size="small"
              icon="iconoir-cancel"
              :loading="cancelling === followUp.id"
              @click="cancel(followUp)"
            >
              {{ $t('agentFollowUps.cancel') }}
            </Button>
          </div>
        </template>
      </AgentConfigurationCard>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'
import { useI18n } from '#imports'
import moment from '@baserow/modules/core/moment'
import { notifyIf } from '@baserow/modules/core/utils/error'
import AgentConfigurationCard from '@baserow_enterprise/components/agentApplication/AgentConfigurationCard'
import AgentKeyValueList from '@baserow_enterprise/components/agentApplication/AgentKeyValueList'
import { useAgentContext } from '@baserow_enterprise/composables/useAgentContext'
import {
  ACTIVE_FOLLOW_UP_STATUS,
  describeWatch,
  followUpFields,
} from '@baserow_enterprise/utils/agentFollowUp'
import { totalTokens } from '@baserow_enterprise/utils/agentUsage'
import AgentUsageSummary from '@baserow_enterprise/components/agentApplication/AgentUsageSummary'

const props = defineProps({
  application: {
    type: Object,
    required: true,
  },
})
const emit = defineEmits(['open-conversation'])

const store = useStore()
const { t } = useI18n()
const { storePrefix, hasPermission } = useAgentContext()

const filters = ['active', 'ended', 'all']
const filterIndex = ref(0)
const filterSegments = computed(() =>
  filters.map((filter) => ({ label: t(`agentFollowUps.filter_${filter}`) }))
)

const followUps = computed(
  () => store.getters[`${storePrefix}agentApplication/getFollowUps`]
)
const loading = computed(
  () => store.getters[`${storePrefix}agentApplication/isFollowUpsLoading`]
)
const visible = computed(() => {
  const filter = filters[filterIndex.value]
  return followUps.value.filter((followUp) => {
    const active = followUp.status === ACTIVE_FOLLOW_UP_STATUS
    return filter === 'all' || (filter === 'active') === active
  })
})

const userId = computed(() => store.getters['auth/getUserId'])
const canManageAnyone = computed(() =>
  hasPermission(
    'agent_application.delete_follow_up',
    props.application,
    props.application.workspace.id
  )
)

// Someone else's private follow-up only shows that it exists.
const isRedacted = (followUp) =>
  followUp.private && followUp.created_by?.id !== userId.value

const canManage = (followUp) =>
  followUp.status === ACTIVE_FOLLOW_UP_STATUS &&
  (followUp.created_by?.id === userId.value || canManageAnyone.value)

const subtitle = (followUp) =>
  followUp.status === ACTIVE_FOLLOW_UP_STATUS
    ? describeWatch(followUp.watch, t)
    : t(`agentFollowUps.status_${followUp.status}`)

const relative = (time) => moment(time).fromNow()

// Opens the check so the person sees what it found, also when nothing
// changed.
const checking = ref(null)
const checkNow = async (followUp) => {
  checking.value = followUp.id
  try {
    const chat = await store.dispatch(
      `${storePrefix}agentApplication/checkFollowUp`,
      { followUpId: followUp.id }
    )
    emit('open-conversation', chat.uuid)
  } catch (error) {
    notifyIf(error, 'application')
  } finally {
    checking.value = null
  }
}

const cancelling = ref(null)
const cancel = async (followUp) => {
  cancelling.value = followUp.id
  try {
    await store.dispatch(`${storePrefix}agentApplication/cancelFollowUp`, {
      followUpId: followUp.id,
    })
  } catch (error) {
    notifyIf(error, 'application')
  } finally {
    cancelling.value = null
  }
}
</script>
