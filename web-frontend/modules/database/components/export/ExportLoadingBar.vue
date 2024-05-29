<template>
  <div class="modal-progress__actions">
    <template v-if="job !== null">
      <ProgressBar :value="job.progress_percentage" :status="job.state" />
    </template>

    <Button
      v-if="job === null || job.state !== 'finished'"
      type="primary"
      size="large"
      :loading="loading"
      :disabled="disabled || loading"
      full-width
      class="modal-progress__export-button"
    >
      {{ $t('exportTableLoadingBar.export') }}
    </Button>
    <DownloadLink
      v-else
      class="button button--large button--full-width modal-progress__export-button"
      :url="job.url"
      :filename="filename"
      :loading-class="'button--loading'"
    >
      <template #default="{ loading: downloadLoading }">
        <template v-if="!downloadLoading">{{
          $t('exportTableLoadingBar.download')
        }}</template>
      </template>
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
