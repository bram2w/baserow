<template>
  <Modal @hidden="stopPollIfRunning()">
    <div v-if="loadingViews" class="loading-overlay"></div>
    <h2 class="box__title">Export {{ table.name }}</h2>
    <Error :error="error"></Error>
    <ExportTableForm
      ref="form"
      :view="view"
      :views="views"
      :loading="loading"
      @submitted="submitted"
      @values-changed="valuesChanged"
    >
      <ExportTableLoadingBar
        :job="job"
        :loading="loading"
        :disabled="!isValid"
      ></ExportTableLoadingBar>
    </ExportTableForm>
  </Modal>
</template>

<script>
import { mapState } from 'vuex'

import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import ExporterService from '@baserow/modules/database/services/export'
import ViewService from '@baserow/modules/database/services/view'
import { populateView } from '@baserow/modules/database/store/view'
import ExportTableForm from '@baserow/modules/database/components/export/ExportTableForm'
import ExportTableLoadingBar from '@baserow/modules/database/components/export/ExportTableLoadingBar'

export default {
  name: 'ExportTableModal',
  components: { ExportTableForm, ExportTableLoadingBar },
  mixins: [modal, error],
  props: {
    table: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      views: [],
      loadingViews: false,
      loading: false,
      job: null,
      pollInterval: null,
      isValid: false,
    }
  },
  computed: {
    jobIsRunning() {
      return (
        this.job !== null && ['exporting', 'pending'].includes(this.job.status)
      )
    },
    jobHasFailed() {
      return ['failed', 'cancelled'].includes(this.job.status)
    },
    ...mapState({
      selectedTableViews: (state) => state.view.items,
    }),
  },
  methods: {
    async show(...args) {
      const show = modal.methods.show.call(this, ...args)
      this.job = null
      this.loading = false
      await this.fetchViews()
      this.$nextTick(() => {
        this.valuesChanged()
      })
      return show
    },
    hide(...args) {
      this.stopPollIfRunning()
      return modal.methods.hide.call(this, ...args)
    },
    async fetchViews() {
      if (this.table._.selected) {
        this.views = this.selectedTableViews
        return
      }

      this.loadingViews = true
      try {
        const { data: viewsData } = await ViewService(this.$client).fetchAll(
          this.table.id
        )
        viewsData.forEach((v) => populateView(v, this.$registry))
        this.views = viewsData
      } catch (error) {
        this.handleError(error, 'views')
      }
      this.loadingViews = false
    },
    async submitted(values) {
      if (!this.$refs.form.isFormValid()) {
        return
      }

      this.loading = true
      this.hideError()

      try {
        const { data } = await ExporterService(this.$client).export(
          this.table.id,
          values
        )
        this.job = data
        if (this.pollInterval !== null) {
          clearInterval(this.pollInterval)
        }
        this.pollInterval = setInterval(this.getLatestJobInfo, 1000)
      } catch (error) {
        this.stopPollAndHandleError(error)
      }
    },
    async getLatestJobInfo() {
      try {
        const { data } = await ExporterService(this.$client).get(this.job.id)
        this.job = data
        if (!this.jobIsRunning) {
          this.loading = false
          this.stopPollIfRunning()
        }
        if (this.jobHasFailed) {
          const title =
            this.job.status === 'failed'
              ? this.$t('exportTableModal.failedTitle')
              : this.$t('exportTableModal.cancelledTitle')
          const message =
            this.job.status === 'failed'
              ? this.$t('exportTableModal.failedDescription')
              : this.$t('exportTableModal.cancelledDescription')
          console.log(title, message)
          this.showError(title, message)
        }
      } catch (error) {
        this.stopPollAndHandleError(error)
      }
    },
    stopPollAndHandleError(error) {
      this.loading = false
      this.stopPollIfRunning()
      this.handleError(error, 'export')
    },
    stopPollIfRunning() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
      }
    },
    valuesChanged() {
      this.isValid = this.$refs.form.isFormValid()
      this.job = null
    },
  },
}
</script>

<i18n>
{
  "en": {
    "exportTableModal": {
      "failedTitle": "Export Failed",
      "failedDescription": "The export failed due to a server error.",
      "cancelledTitle": "Export Cancelled",
      "cancelledDescription": "The export was cancelled."
    }
  },
  "fr": {
    "exportTableModal": {
      "failedTitle": "L'export a échoué",
      "failedDescription": "L'export n'a pas pu aboutir en raison d'une erreur serveur.",
      "cancelledTitle": "Export annulé",
      "cancelledDescription": "L'export a été annulé."
    }
  }
}
</i18n>
