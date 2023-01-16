<template>
  <div class="modal-progress__actions">
    <template v-if="job !== null">
      <ProgressBar :value="job.progress_percentage" :status="job.state" />
    </template>
    <button
      v-if="job === null || job.state !== 'finished'"
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
  name: 'ExportLoadingBar',
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
}
</script>
