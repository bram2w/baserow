<template>
  <a
    :class="{
      'context__menu-item--loading': loading,
      disabled: disabled || loading,
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
      loading: false,
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
      this.loading = false
      this.showError(
        this.$t('clientHandler.notCompletedTitle'),
        this.$t('clientHandler.notCompletedDescription')
      )
    },
    // eslint-disable-next-line require-await
    async onJobPollingError(error) {
      this.loading = false
      notifyIf(error, 'table')
    },
    async onJobDone() {
      const database = this.database
      const table = this.job.duplicated_table
      await this.$store.dispatch('table/forceCreate', {
        database,
        data: table,
      })
      this.loading = false
      this.$emit('table-duplicated', { table })
    },
    async duplicateTable() {
      if (this.loading || this.disabled) {
        return
      }

      this.loading = true
      try {
        const { data: job } = await TableService(this.$client).asyncDuplicate(
          this.table.id
        )
        this.startJobPoller(job)
      } catch (error) {
        this.loading = false
        notifyIf(error, 'table')
      }
    },
  },
}
</script>
