<template>
  <div>
    <Error :error="error"></Error>
    <Alert v-if="errorReport.length > 0 && error.visible" type="warning">
      <template #title>{{
        $t('importErrorReport.reportTitleFailure')
      }}</template>

      {{ $t('importErrorReport.reportMessage') }}
      {{ errorReport.join(', ') }}
    </Alert>
    <Alert v-if="errorReport.length > 0 && !error.visible" type="warning">
      <template #title>
        {{ $t('importErrorReport.reportTitleSuccess') }}</template
      >

      {{ $t('importErrorReport.reportMessage') }}
      {{ errorReport.join(', ') }}
    </Alert>
  </div>
</template>

<script>
export default {
  name: 'ImportErrorReport',
  props: {
    error: {
      type: Object,
      required: true,
    },
    job: {
      validator: (prop) => typeof prop === 'object' || prop === null,
      required: true,
    },
  },
  computed: {
    errorReport() {
      if (this.job && Object.keys(this.job.report.failing_rows).length > 0) {
        return Object.keys(this.job.report.failing_rows)
          .map((key) => parseInt(key, 10) + 1)
          .sort((a, b) => a - b)
      } else {
        return []
      }
    },
  },
}
</script>
