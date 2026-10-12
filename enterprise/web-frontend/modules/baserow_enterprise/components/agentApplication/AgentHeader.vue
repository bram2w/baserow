<template>
  <header class="layout__col-2-1 header header--space-between">
    <div class="agent-page__header-title">
      <i class="agent-page__header-icon baserow-icon-agent"></i>
      <span class="agent-page__header-name">
        {{ application.name }}
      </span>
      <ul
        v-if="!template"
        v-skeleton="loading"
        data-allow-mismatch="class,style,attribute"
        class="header__filter agent-page__header-approvals"
      >
        <li class="header__filter-item">
          <a
            ref="approvalsButton"
            class="header__filter-link agent-page__header-approvals-link"
            :class="{
              'agent-page__header-approvals-link--pending':
                pendingApprovalsCount > 0,
            }"
            @click="toggleApprovalsContext"
          >
            <i
              class="header__filter-icon iconoir-check-circle agent-page__header-approvals-icon"
            ></i>
            <span class="header__filter-name">{{
              $t('agentHeader.approvalsWaiting', {
                count: pendingApprovalsCount,
              })
            }}</span>
          </a>
        </li>
      </ul>
      <AgentPendingApprovalsContext
        v-if="!template"
        ref="approvalsContext"
        :application="application"
        @open-conversation="$emit('open-conversation', $event)"
      />
    </div>
    <div class="header__right">
      <div class="header__buttons header__buttons--with-separator">
        <span
          v-if="!template"
          v-skeleton="loading"
          data-allow-mismatch="class,style,attribute"
          class="agent-page__header-last-run"
        >
          {{
            application.last_run_on
              ? $t('agentHeader.lastRun', { time: lastRun })
              : $t('agentHeader.neverRan')
          }}
        </span>
        <ButtonIcon
          icon="iconoir-settings"
          :active="configurationOpen"
          :title="$t('agentHeader.configure')"
          @click="$emit('toggle-configuration')"
        ></ButtonIcon>
      </div>
    </div>
  </header>
</template>

<script>
import { defineComponent, computed, ref } from 'vue'
import { useStore } from 'vuex'
import moment from '@baserow/modules/core/moment'
import AgentPendingApprovalsContext from '@baserow_enterprise/components/agentApplication/AgentPendingApprovalsContext'
import { useAgentContext } from '@baserow_enterprise/composables/useAgentContext'

export default defineComponent({
  name: 'AgentHeader',
  components: { AgentPendingApprovalsContext },
  props: {
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
    application: {
      type: Object,
      required: true,
    },
    configurationOpen: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['toggle-configuration', 'open-conversation'],
  setup(props) {
    const store = useStore()
    const { storePrefix, template } = useAgentContext()

    const agent = computed(
      () => store.getters[`${storePrefix}agentApplication/getAgent`]
    )

    // Driven by the application object in the core store, so the workspace
    // wide `agent_pending_approvals_updated` websocket event updates it live.
    const pendingApprovalsCount = computed(
      () => props.application.pending_approvals_count || 0
    )

    const approvalsButton = ref(null)
    const approvalsContext = ref(null)
    const toggleApprovalsContext = () => {
      approvalsContext.value.toggle(approvalsButton.value, 'bottom', 'left', 4)
    }

    const lastRun = computed(() =>
      moment(props.application.last_run_on).calendar()
    )

    return {
      template,
      agent,
      lastRun,
      pendingApprovalsCount,
      approvalsButton,
      approvalsContext,
      toggleApprovalsContext,
    }
  },
})
</script>
