<template>
  <div class="public-dashboard">
    <div
      class="public-dashboard__content dashboard-app__content"
      :class="{ 'dashboard-app__content--with-widgets': !isEmpty }"
    >
      <div class="public-dashboard__main">
        <div class="dashboard-app__content-header">
          <div class="dashboard-app__content-header-main">
            <div class="dashboard-app__title">{{ dashboard.name }}</div>
            <div
              v-if="dashboard.description"
              class="dashboard-app__description"
            >
              {{ dashboard.description }}
            </div>
          </div>
        </div>
        <DashboardWidgetGridLoading v-if="loading" />
        <div v-else-if="isEmpty" class="public-dashboard__empty">
          {{ $t('publicDashboard.noWidgets') }}
        </div>
        <WidgetBoard v-else :dashboard="dashboard" />
      </div>
      <div v-if="dashboard.show_logo" class="public-dashboard__footer">
        <ExternalLinkBaserowLogo />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'
import ExternalLinkBaserowLogo from '@baserow/modules/core/components/ExternalLinkBaserowLogo'
import DashboardWidgetGridLoading from '@baserow/modules/dashboard/components/DashboardWidgetGridLoading'
import WidgetBoard from '@baserow/modules/dashboard/components/WidgetBoard'

/**
 * Renders a publicly shared dashboard for its visitors: the name, the
 * description and the read-only widget grid. The widgets and their data live in
 * the `dashboardApplication` store, in its public mode.
 */
defineProps({
  dashboard: {
    type: Object,
    required: true,
  },
  loading: {
    type: Boolean,
    required: false,
    default: false,
  },
})

const store = useStore()

const isEmpty = computed(() => store.getters['dashboardApplication/isEmpty'])
</script>
