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
      Export
    </button>
    <a
      v-else
      class="
        button button--large button--success
        export-table-modal__export-button
      "
      :href="job.url"
      target="_blank"
    >
      Download
    </a>
  </div>
</template>

<script>
export default {
  name: 'ExportTableLoadingBar',
  props: {
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
