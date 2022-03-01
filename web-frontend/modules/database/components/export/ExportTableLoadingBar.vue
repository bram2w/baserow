<template>
  <div class="export-table-modal__actions">
    <div v-if="job !== null" class="export-table-modal__loading-bar">
      <div
        class="export-table-modal__loading-bar-inner"
        :style="{
          width: `${job.progress_percentage * 100}%`,
          'transition-duration': [1, 0].includes(job.progress_percentage)
            ? '0s'
            : '1s',
        }"
      ></div>
      <span v-if="jobIsRunning" class="export-table-modal__status-text">
        {{ job.status }}
      </span>
    </div>
    <button
      v-if="job === null || job.status !== 'complete'"
      class="
        button button--large button--primary
        export-table-modal__export-button
      "
      :class="{ 'button--loading': loading }"
      :disabled="disabled"
    >
      {{ $t('exportTableLoadingBar.export') }}
    </button>
    <DownloadLink
      v-else
      class="
        button button--large button--success
        export-table-modal__export-button
      "
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
