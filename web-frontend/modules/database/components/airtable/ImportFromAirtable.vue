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
          {{ $t(importFromAirtable.linkError) }}
        </div>
      </div>
    </div>
    <Error :error="error"></Error>
    <div class="modal-progress__actions">
      <ProgressBar
        v-if="jobIsRunning || jobHasSucceeded"
        :value="job.progress_percentage"
        :status="jobHumanReadableState"
      />
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
import jobProgress from '@baserow/modules/core/mixins/jobProgress'
import AirtableService from '@baserow/modules/database/services/airtable'

export default {
  name: 'ImportFromAirtable',
  mixins: [error, jobProgress],
  data() {
    return {
      importType: 'none',
      airtableUrl: '',
      loading: false,
    }
  },
  computed: {
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
          this.airtableUrl
        )
        this.startJobPoller(data)
      } catch (error) {
        this.stopPollAndHandleError(error, {
          ERROR_MAX_JOB_COUNT_EXCEEDED: new ResponseErrorMessage(
            this.$t('importFromAirtable.errorJobAlreadyRunningTitle'),
            this.$t('importFromAirtable.errorJobAlreadyRunningDescription')
          ),
        })
      }
    },
    stopPollAndHandleError(error, specificErrorMap = null) {
      this.loading = false
      this.stopPollIfRunning()
      error.handler
        ? this.handleError(error, 'airtable', specificErrorMap)
        : this.showError(error)
    },
    getCustomHumanReadableJobState(state) {
      const importingTablePrefix = 'importing-table-'
      if (state.startsWith(importingTablePrefix)) {
        const table = state.replace(importingTablePrefix, '')
        return this.$t('importFromAirtable.stateImportingTable', { table })
      }

      const translations = {
        'downloading-base': this.$t('importFromAirtable.stateDownloadingBase'),
        converting: this.$t('importFromAirtable.stateConverting'),
        'downloading-files': this.$t(
          'importFromAirtable.stateDownloadingFiles'
        ),
        importing: this.$t('importFromAirtable.stateImporting'),
      }
      return translations[state]
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
    onJobFailed() {
      const error = new ResponseErrorMessage(
        this.$t('importFromAirtable.importError'),
        this.job.human_readable_error
      )
      this.stopPollAndHandleError(error)
    },
    onJobPollingError(error) {
      this.stopPollAndHandleError(error)
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
