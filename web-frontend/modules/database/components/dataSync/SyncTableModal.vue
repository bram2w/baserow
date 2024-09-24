<template>
  <Modal :can-close="!jobIsRunning" @hidden="hidden">
    <template #content>
      <div class="import-modal__header">
        <h2 class="import-modal__title">
          {{ $t('syncTableModal.title', { name: table.name }) }}
        </h2>
      </div>
      <p>
        {{ $t('syncTableModal.description') }}
      </p>
      <Error :error="error"></Error>
      <div class="modal-progress__actions margin-top-2">
        <ProgressBar
          v-if="jobIsRunning || jobHasSucceeded"
          :value="job.progress_percentage"
          :status="jobHumanReadableState"
        />
        <div class="align-right">
          <Button
            v-if="!jobHasSucceeded"
            type="primary"
            size="large"
            :disabled="creatingJob || jobIsRunning"
            :loading="creatingJob || jobIsRunning"
            @click="sync"
          >
            {{ $t('syncTableModal.sync') }}
          </Button>
          <Button v-else type="secondary" size="large" @click="hide()">{{
            $t('syncTableModal.hide')
          }}</Button>
        </div>
      </div>
    </template>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import jobProgress from '@baserow/modules/core/mixins/jobProgress'
import DataSyncService from '@baserow/modules/database/services/dataSync'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'

export default {
  name: 'SyncTableModal',
  mixins: [modal, error, jobProgress],
  props: {
    table: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      creatingJob: false,
    }
  },
  beforeDestroy() {
    this.stopPollIfRunning()
  },
  methods: {
    show() {
      this.job = null
      modal.methods.show.bind(this)()
    },
    hidden() {
      this.stopPollIfRunning()
    },
    async sync() {
      if (this.jobIsRunning) {
        return
      }

      this.hideError()
      this.job = null
      this.creatingJob = true

      try {
        const { data: job } = await DataSyncService(this.$client).syncTable(
          this.table.data_sync.id
        )
        this.startJobPoller(job)
      } catch (error) {
        this.handleError(error)
      } finally {
        this.creatingJob = false
      }
    },
    onJobFailed() {
      const error = new ResponseErrorMessage(
        this.$t('createDataSync.error'),
        this.job.human_readable_error
      )
      this.stopPollAndHandleError(error)
    },
    onJobPollingError(error) {
      this.stopPollAndHandleError(error)
    },
    stopPollAndHandleError(error) {
      this.stopPollIfRunning()
      error.handler ? this.handleError(error) : this.showError(error)
    },
  },
}
</script>
