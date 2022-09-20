<template>
  <a
    :class="{
      'context__menu-item--loading': duplicating,
      disabled: disabled || duplicating,
    }"
    @click="duplicateTable()"
  >
    <i class="context__menu-icon fas fa-fw fa-copy"></i>
    {{ $t('action.duplicate') }}
  </a>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import TableService from '@baserow/modules/database/services/table'
import jobProgress from '@baserow/modules/core/mixins/jobProgress'

export default {
  name: 'SidebarDuplicateTableContextItem',
  mixins: [jobProgress],
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
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
      notifyIf(error, 'table')
    },
    async onJobUpdated() {
      await this.$store.dispatch('job/forceUpdate', {
        job: this.job,
        data: this.job,
      })
    },
    async onJobDone() {
      await this.$store.dispatch('job/forceUpdate', {
        job: this.job,
        data: this.job,
      })
      this.duplicating = false
    },
    async duplicateTable() {
      if (this.duplicating || this.disabled) {
        return
      }

      this.duplicating = true
      try {
        const { data: job } = await TableService(this.$client).asyncDuplicate(
          this.table.id
        )
        this.startJobPoller(job)
        this.$store.dispatch('job/forceCreate', job)
      } catch (error) {
        this.duplicating = false
        notifyIf(error, 'table')
      }
      this.$emit('click')
    },
  },
}
</script>
