<template>
  <div class="modal-progress__actions">
    <template v-if="job !== null">
      <ProgressBar
        :value="job.progress_percentage * 100"
        :status="job.status"
      />
    </template>
    <button
      v-if="job === null || job.status !== 'complete'"
      class="button button--large button--primary modal-progress__export-button"
      :class="{ 'button--loading': loading }"
      :disabled="disabled"
    >
      {{ $t('exportTableLoadingBar.export') }}
    </button>
    <DownloadLink
      v-else
      class="button button--large button--success modal-progress__export-button"
      :url="job.url"
      :filename="filename"
      :loading-class="'button--loading'"
    >
      {{ $t('exportTableLoadingBar.download') }}
    </DownloadLink>
  </div>
</template>

<script>
export default {
  name: 'ExportTableLoadingBar',
  props: {
    filename: {
      type: String,
      required: false,
      default: 'export',
    },
    exportType: {
      type: String,
      required: false,
      default: 'export',
    },
    job: {
      type: Object,
      required: false,
      default: null,
    },
    loading: {
      type: Boolean,
      required: true,
    },
    disabled: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    jobIsRunning() {
      return (
        this.job !== null && ['exporting', 'pending'].includes(this.job.status)
      )
    },
  },
}
</script>
