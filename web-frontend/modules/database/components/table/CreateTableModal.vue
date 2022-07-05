<template>
  <Modal @show="reset()">
    <h2 class="box__title">{{ $t('createTableModal.title') }}</h2>
    <TableForm ref="tableForm" @submitted="submitted">
      <div class="control">
        <label class="control__label">
          {{ $t('createTableModal.importLabel') }}
        </label>
        <div class="control__elements">
          <ul class="choice-items">
            <li>
              <a
                class="choice-items__link"
                :class="{ active: importer === '' }"
                @click=";[(importer = ''), reset()]"
              >
                <i class="choice-items__icon fas fa-clone"></i>
                {{ $t('createTableModal.newTable') }}
              </a>
            </li>
            <li v-for="importerType in importerTypes" :key="importerType.type">
              <a
                class="choice-items__link"
                :class="{ active: importer === importerType.type }"
                @click=";[(importer = importerType.type), reset()]"
              >
                <i
                  class="choice-items__icon fas"
                  :class="'fa-' + importerType.iconClass"
                ></i>
                {{ importerType.getName() }}
              </a>
            </li>
          </ul>
        </div>
      </div>
      <component
        :is="importerComponent"
        :disabled="importInProgress"
        @changed="reset()"
      />
      <Error :error="error"></Error>
      <Alert
        v-if="errorReport.length > 0 && error.visible"
        :title="$t('createTableModal.reportTitleFailure')"
        type="warning"
        icon="exclamation"
      >
        {{ $t('createTableModal.reportMessage') }} {{ errorReport.join(', ') }}
      </Alert>
      <Alert
        v-if="errorReport.length > 0 && !error.visible"
        :title="$t('createTableModal.reportTitleSuccess')"
        type="warning"
        icon="exclamation"
      >
        {{ $t('createTableModal.reportMessage') }} {{ errorReport.join(', ') }}
      </Alert>
      <div v-if="!jobHasSucceeded" class="modal-progress__actions">
        <ProgressBar
          v-if="importInProgress && showProgressBar"
          :value="progressPercentage"
          :status="humanReadableState"
        />
        <div class="align-right">
          <button
            class="button button--large"
            :class="{ 'button--loading': importInProgress }"
            :disabled="importInProgress"
          >
            {{ $t('createTableModal.addButton') }}
          </button>
        </div>
      </div>
      <div v-else class="align-right">
        <button
          class="button button--large button--success"
          @click.prevent="openTable"
        >
          {{ $t('createTableModal.openCreatedTable') }}
        </button>
      </div>
    </TableForm>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import jobProgress from '@baserow/modules/core/mixins/jobProgress'

import JobService from '@baserow/modules/core/services/job'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'
import TableForm from './TableForm'

export default {
  name: 'CreateTableModal',
  components: { TableForm },
  mixins: [modal, error, jobProgress],
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      importer: '',
      uploadProgressPercentage: 0,
      importState: null,
      showProgressBar: false,
    }
  },
  computed: {
    progressPercentage() {
      switch (this.state) {
        case null:
          return 0
        case 'preparingData':
          return 1
        case 'uploading':
          // 10% -> 50%
          return (this.uploadProgressPercentage / 100) * 40 + 10
        default:
          // 50% -> 100%
          return 50 + this.job.progress_percentage / 2
      }
    },
    state() {
      if (this.job === null) {
        return this.importState
      } else {
        return this.job.state
      }
    },
    importInProgress() {
      return this.state !== null && !this.jobIsFinished && !this.error.visible
    },
    importerTypes() {
      return this.$registry.getAll('importer')
    },
    importerComponent() {
      return this.importer === ''
        ? null
        : this.$registry.get('importer', this.importer).getFormComponent()
    },
    humanReadableState() {
      switch (this.state) {
        case null:
          return ''
        case 'preparingData':
          return this.$t('createTableModal.preparing')
        case 'uploading':
          if (this.uploadProgressPercentage === 100) {
            return this.$t('job.statePending')
          } else {
            return this.$t('createTableModal.uploading')
          }
        default:
          return this.jobHumanReadableState
      }
    },
    errorReport() {
      if (this.job && Object.keys(this.job.report.failing_rows).length > 0) {
        return Object.keys(this.job.report.failing_rows)
          .map((key) => parseInt(key, 10))
          .sort((a, b) => a - b)
      } else {
        return []
      }
    },
  },
  beforeDestroy() {
    this.stopPollIfRunning()
  },
  methods: {
    reset() {
      this.job = null
      this.importState = null
      this.uploadProgressPercentage = 0
      this.hideError()
    },
    /**
     * When the form is submitted we try to extract the initial data and first row
     * header setting from the values. An importer could have added those, but they
     * need to be removed from the values.
     */
    async submitted(values) {
      this.showProgressBar = false
      this.reset()

      let firstRowHeader = false
      let data = null

      if (Object.prototype.hasOwnProperty.call(values, 'firstRowHeader')) {
        firstRowHeader = values.firstRowHeader
        delete values.firstRowHeader
      }

      if (
        Object.prototype.hasOwnProperty.call(values, 'getData') &&
        typeof values.getData === 'function'
      ) {
        try {
          this.showProgressBar = true
          this.importState = 'preparingData'
          await this.$ensureRender()

          data = await values.getData()
          delete values.getData
        } catch (error) {
          this.reset()
          this.handleError(error, 'application')
        }
      }

      this.importState = 'uploading'

      try {
        if (data && data.length > 0) {
          this.showProgressBar = true
        }
        const jobId = await this.$store.dispatch('table/create', {
          database: this.application,
          values,
          initialData: data,
          firstRowHeader,
          onUploadProgress: ({ loaded, total }) =>
            (this.uploadProgressPercentage = (loaded / total) * 100),
        })

        const { data: job } = await JobService(this.$client).get(jobId)
        this.startJobPoller(job)
      } catch (error) {
        this.stopPollAndHandleError(error, {
          ERROR_MAX_JOB_COUNT_EXCEEDED: new ResponseErrorMessage(
            this.$t('job.errorJobAlreadyRunningTitle'),
            this.$t('job.errorJobAlreadyRunningDescription')
          ),
        })
      }
    },
    getCustomHumanReadableJobState(jobState) {
      const translations = {
        'file-import-row-creation': this.$t(
          'createTableModal.stateRowCreation'
        ),
        'file-import-pre-validation': this.$t(
          'createTableModal.statePreValidation'
        ),
        'file-import-create-table': this.$t(
          'createTableModal.stateCreateTable'
        ),
      }
      return translations[jobState]
    },
    openTable() {
      // Redirect to the newly created table.
      this.$nuxt.$router.push({
        name: 'database-table',
        params: {
          databaseId: this.application.id,
          tableId: this.job.table_id,
        },
      })
      this.hide()
    },
    onJobFailure() {
      const error = new ResponseErrorMessage(
        this.$t('createTableModal.importError'),
        this.job.human_readable_error
      )
      this.stopPollAndHandleError(error)
    },
    onJobError(error) {
      this.stopPollAndHandleError(error)
    },
    stopPollAndHandleError(error, specificErrorMap = null) {
      this.stopPollIfRunning()
      error.handler
        ? this.handleError(error, 'application', specificErrorMap)
        : this.showError(error)
    },
  },
}
</script>
