<template>
  <div>
    <div class="control">
      <label class="control__label">
        {{ $t('importFromAirtable.airtableShareLinkTitle') }}
      </label>
      <p class="margin-bottom-2">
        {{ $t('importFromAirtable.airtableShareLinkDescription') }}
        <br /><br />
        {{ $t('importFromAirtable.airtableShareLinkBeta') }}
      </p>
      <div class="control__elements">
        <input
          ref="airtableUrl"
          v-model="airtableUrl"
          :class="{ 'input--error': $v.airtableUrl.$error }"
          type="text"
          class="input input--large"
          :placeholder="$t('importFromAirtable.airtableShareLinkPaste')"
          @blur="$v.airtableUrl.$touch()"
        />
        <div v-if="$v.airtableUrl.$error" class="error">
          The link should look like: https://airtable.com/shrxxxxxxxxxxxxxx
        </div>
      </div>
    </div>
    <Error :error="error"></Error>
    <div class="modal-progress__actions">
      <div
        v-if="jobIsRunning || jobHasSucceeded"
        class="modal-progress__loading-bar"
      >
        <div
          class="modal-progress__loading-bar-inner"
          :style="{
            width: `${job.progress_percentage}%`,
            'transition-duration': [1, 0].includes(job.progress_percentage)
              ? '0s'
              : '1s',
          }"
        ></div>
        <span class="modal-progress__status-text">
          {{ humanReadableState }}
        </span>
      </div>
      <button
        v-if="!jobHasSucceeded"
        class="button button--large modal-progress__export-button"
        :class="{ 'button--loading': loading }"
        :disabled="loading"
        @click="importFromAirtable"
      >
        {{ $t('importFromAirtable.importButtonLabel') }}
      </button>
      <button
        v-else
        class="
          button button--large button--success
          modal-progress__export-button
        "
        @click="openDatabase"
      >
        {{ $t('importFromAirtable.openButtonLabel') }}
      </button>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'
import error from '@baserow/modules/core/mixins/error'
import AirtableService from '@baserow/modules/database/services/airtable'

export default {
  name: 'ImportFromAirtable',
  mixins: [error],
  data() {
    return {
      importType: 'none',
      airtableUrl: '',
      loading: false,
      job: null,
      pollInterval: null,
    }
  },
  computed: {
    jobHasSucceeded() {
      return this.job !== null && this.job.state === 'finished'
    },
    jobIsRunning() {
      return (
        this.job !== null && !['failed', 'finished'].includes(this.job.state)
      )
    },
    jobHasFailed() {
      return this.job !== null && this.job.state === 'failed'
    },
    humanReadableState() {
      if (this.job === null) {
        return ''
      }

      const importingTablePrefix = 'importing-table-'
      if (this.job.state.startsWith(importingTablePrefix)) {
        const table = this.job.state.replace(importingTablePrefix, '')
        return this.$t('importFromAirtable.stateImportingTable', { table })
      }

      const translations = {
        pending: this.$t('importFromAirtable.statePending'),
        failed: this.$t('importFromAirtable.stateFailed'),
        finished: this.$t('importFromAirtable.stateFinished'),
        'downloading-base': this.$t('importFromAirtable.stateDownloadingBase'),
        converting: this.$t('importFromAirtable.stateConverting'),
        'downloading-files': this.$t(
          'importFromAirtable.stateDownloadingFiles'
        ),
        importing: this.$t('importFromAirtable.stateImporting'),
      }
      return translations[this.job.state]
    },
    ...mapGetters({
      selectedGroupId: 'group/selectedId',
    }),
  },
  beforeDestroy() {
    this.stopPollIfRunning()
  },
  methods: {
    async importFromAirtable() {
      this.$v.$touch()
      if (this.$v.$invalid && !this.loading) {
        return
      }

      this.loading = true
      this.hideError()

      try {
        const { data } = await AirtableService(this.$client).create(
          this.selectedGroupId,
          this.airtableUrl,
          new Intl.DateTimeFormat().resolvedOptions().timeZone
        )
        this.job = data
        this.pollInterval = setInterval(this.getLatestJobInfo, 1000)
      } catch (error) {
        this.stopPollAndHandleError(error, {
          ERROR_AIRTABLE_JOB_ALREADY_RUNNING: new ResponseErrorMessage(
            this.$t('importFromAirtable.errorJobAlreadyRunningTitle'),
            this.$t('importFromAirtable.errorJobAlreadyRunningDescription')
          ),
        })
        this.loading = false
      }
    },
    async getLatestJobInfo() {
      try {
        const { data } = await AirtableService(this.$client).get(this.job.id)
        this.job = data
        if (this.jobHasFailed) {
          const error = new ResponseErrorMessage(
            this.$t('importFromAirtable.importError'),
            this.job.human_readable_error
          )
          this.stopPollAndHandleError(error)
        } else if (!this.jobIsRunning) {
          this.stopPollIfRunning()
        }
      } catch (error) {
        this.stopPollAndHandleError(error)
      }
    },
    stopPollAndHandleError(error, specificErrorMap = null) {
      this.loading = false
      this.stopPollIfRunning()
      error.handler
        ? this.handleError(error, 'airtable', specificErrorMap)
        : this.showError(error)
    },
    stopPollIfRunning() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
      }
    },
    openDatabase() {
      const application = this.$store.getters['application/get'](
        this.job.database.id
      )
      const type = this.$registry.get('application', application.type)
      if (type.select(application, this)) {
        this.$emit('hidden')
      }
    },
  },
  validations: {
    airtableUrl: {
      valid(value) {
        const regex = /https:\/\/airtable.com\/shr(.*)$/g
        return !!value.match(regex)
      },
    },
  },
}
</script>
