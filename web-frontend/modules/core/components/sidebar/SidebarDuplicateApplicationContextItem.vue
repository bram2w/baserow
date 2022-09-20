<template>
  <a
    :class="{
      'context__menu-item--loading': duplicating,
      disabled: disabled || duplicating,
    }"
    @click="duplicateApplication()"
  >
    <i class="context__menu-icon fas fa-fw fa-copy"></i>
    {{
      $t('sidebarApplication.duplicate', {
        type: application._.type.name.toLowerCase(),
      })
    }}
  </a>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import ApplicationService from '@baserow/modules/core/services/application'
import jobProgress from '@baserow/modules/core/mixins/jobProgress'

export default {
  name: 'SidebarDuplicateApplicationContextItem',
  mixins: [jobProgress],
  props: {
    application: {
      type: Object,
      required: true,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      duplicating: false,
    }
  },
  methods: {
    showError(title, message) {
      this.$store.dispatch(
        'notification/error',
        { title, message },
        { root: true }
      )
    },
    // eslint-disable-next-line require-await
    async onJobFailed() {
      await this.$store.dispatch('job/forceUpdate', {
        job: this.job,
        data: this.job,
      })

      this.duplicating = false
    },
    async onJobPollingError(error) {
      await this.$store.dispatch('job/forceDelete', this.job)
      this.duplicating = false
      notifyIf(error, 'application')
    },
    async onJobUpdated() {
      await this.$store.dispatch('job/forceUpdate', {
        job: this.job,
        data: this.job,
      })
    },
    // eslint-disable-next-line require-await
    async onJobDone() {
      await this.$store.dispatch('job/forceUpdate', {
        job: this.job,
        data: this.job,
      })
      this.duplicating = false
    },
    async duplicateApplication() {
      if (this.duplicating || this.disabled) {
        return
      }

      this.duplicating = true
      try {
        const { data: job } = await ApplicationService(
          this.$client
        ).asyncDuplicate(this.application.id)
        this.startJobPoller(job)
        this.$store.dispatch('job/forceCreate', job)
      } catch (error) {
        this.duplicating = false
        notifyIf(error, 'application')
      }
      this.$emit('click')
    },
  },
}
</script>
