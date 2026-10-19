<template>
  <div>
    <a
      ref="contextLink"
      class="header__filter-link"
      :class="{ 'active active--primary': dashboard.public }"
      @click="context.toggle(contextLink, 'bottom', 'left', 4)"
    >
      <i class="header__filter-icon iconoir-link"></i>
      <span class="header__filter-name">
        {{ $t('shareDashboardLink.shareDashboard') }}
      </span>
    </a>

    <Context ref="context" max-height-if-outside-viewport>
      <div class="dashboard-sharing">
        <div v-if="!dashboard.public" class="dashboard-sharing__share-link">
          <div class="dashboard-sharing__share-link-title">
            {{ $t('shareDashboardLink.notSharedTitle') }}
          </div>
          <p class="dashboard-sharing__share-link-description">
            {{ $t('shareDashboardLink.notSharedText') }}
          </p>
          <Button
            type="secondary"
            icon="iconoir-link"
            :loading="loading"
            :disabled="loading"
            @click.stop="updateDashboard({ public: true })"
          >
            {{ $t('shareDashboardLink.createPrivateLink') }}
          </Button>
        </div>

        <template v-else>
          <div class="dashboard-sharing__shared-link">
            <div class="dashboard-sharing__shared-link-title">
              {{ $t('shareDashboardLink.sharedTitle') }}
            </div>
            <div class="dashboard-sharing__shared-link-description">
              {{ $t('shareDashboardLink.sharedDescription') }}
            </div>

            <div class="dashboard-sharing__shared-link-content">
              <div class="dashboard-sharing__shared-link-box">
                {{ shareUrl }}
              </div>
              <a
                v-tooltip="$t('shareDashboardLink.copyURL')"
                class="dashboard-sharing__shared-link-action"
                @click="copyShareUrlToClipboard()"
              >
                <i class="iconoir-copy" />
                <Copied ref="copied"></Copied>
              </a>
              <a
                v-tooltip="$t('shareDashboardLink.generateNewUrl')"
                class="dashboard-sharing__shared-link-action"
                @click.prevent="rotateSlugModal.show()"
              >
                <i class="iconoir-refresh-double" />
              </a>
            </div>

            <div
              v-if="additionalShareLinkOptions.length > 0"
              class="dashboard-sharing__shared-link-options"
            >
              <component
                :is="component"
                v-for="(component, i) in additionalShareLinkOptions"
                :key="i"
                :dashboard="dashboard"
                @update-dashboard="forceUpdateDashboard"
              />
            </div>
          </div>

          <div class="context__footer">
            <ButtonText
              icon="iconoir-cancel"
              @click.stop="updateDashboard({ public: false })"
            >
              {{ $t('shareDashboardLink.disableLink') }}
            </ButtonText>
          </div>
        </template>

        <!--
          Kept inside the context so that clicks in the modal count as clicks
          inside the context and don't close it.
        -->
        <DashboardRotateSlugModal
          ref="rotateSlugModal"
          :dashboard="dashboard"
        />
      </div>
    </Context>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useNuxtApp } from '#app'
import DashboardRotateSlugModal from '@baserow/modules/dashboard/components/sharing/DashboardRotateSlugModal'
import { copyToClipboard } from '@baserow/modules/database/utils/clipboard'
import { notifyIf } from '@baserow/modules/core/utils/error'

const props = defineProps({
  dashboard: {
    type: Object,
    required: true,
  },
})

const { $store, $registry, $config } = useNuxtApp()

const context = ref(null)
const contextLink = ref(null)
const copied = ref(null)
const rotateSlugModal = ref(null)
const loading = ref(false)

const shareUrl = computed(() => {
  // The public dashboard page and its route are added together with the
  // anonymous access, so the path is built by hand instead of being resolved
  // through the router.
  return `${$config.public.baserowEmbeddedShareUrl}/public/dashboard/${props.dashboard.slug}`
})

const additionalShareLinkOptions = computed(() => {
  return Object.values($registry.getAll('plugin'))
    .flatMap((plugin) => plugin.getAdditionalDashboardShareLinkOptions())
    .filter((component) => component !== null)
})

const copyShareUrlToClipboard = () => {
  copyToClipboard(shareUrl.value)
  copied.value.show()
}

const updateDashboard = async (values) => {
  const application = props.dashboard
  loading.value = true
  $store.dispatch('application/setItemLoading', { application, value: true })

  try {
    await $store.dispatch('application/update', { application, values })
  } catch (error) {
    notifyIf(error, 'application')
  } finally {
    loading.value = false
    $store.dispatch('application/setItemLoading', { application, value: false })
  }
}

/**
 * Applies values that were already saved by another endpoint, like the premium
 * dashboard attributes, to the dashboard in the store.
 */
const forceUpdateDashboard = (data) => {
  $store.dispatch('application/forceUpdate', {
    application: props.dashboard,
    data,
  })
}
</script>
