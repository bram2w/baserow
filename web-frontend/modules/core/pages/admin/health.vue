<template>
  <div class="layout__col-2-scroll">
    <div class="admin-health">
      <h1>
        {{ $t('health.title') }}
      </h1>
      <div class="admin-health__group">
        <div class="admin-health__description">
          {{ $t('health.description') }}
        </div>
        <div>
          <div
            v-for="(status, checkName) in healthChecks"
            :key="status"
            class="admin-health__check-item"
          >
            <div class="admin-health__check-item-label">
              <div class="admin-health__check-item-name">
                {{ camelCaseToSpaceSeparated(checkName) }}
              </div>
            </div>
            <div
              class="admin-health__icon"
              :class="status !== 'working' ? 'warning' : ''"
            >
              <i
                class="fas"
                :class="
                  status === 'working'
                    ? 'fa-check admin-health__icon--success'
                    : 'fa-times admin-health__icon--fail'
                "
              ></i>
              <div
                v-if="status !== 'working'"
                class="admin-health__check-item-description"
              >
                {{ status }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="admin-health__group">
        <EmailerTester></EmailerTester>
      </div>
    </div>
  </div>
</template>

<script>
import HealthService from '@baserow/modules/core/services/health'
import EmailerTester from '@baserow/modules/core/components/health/EmailTester.vue'

export default {
  components: { EmailerTester },
  layout: 'app',
  middleware: 'staff',
  async asyncData({ app }) {
    const { data } = await HealthService(app.$client).getAll()
    return { healthChecks: data.checks }
  },
  methods: {
    camelCaseToSpaceSeparated(camelCaseString) {
      if (!camelCaseString) {
        return 'unknown'
      } else {
        camelCaseString = camelCaseString.toString()
      }
      return camelCaseString.replace(/([A-Z])/g, ' $1')
    },
  },
}
</script>
