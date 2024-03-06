<template>
  <Modal
    :right-sidebar="!isTableCreation"
    :right-sidebar-scrollable="true"
    :close-button="false"
    :content-scrollable="true"
    @show=";[(importer = ''), reset()]"
    @hide="stopPollIfRunning()"
  >
    <template #content>
      <div class="import-modal__header">
        <h2 class="import-modal__title">
          {{
            isTableCreation
              ? $t('importFileModal.title')
              : $t('importFileModal.additionalImportTitle', {
                  table: table.name,
                })
          }}
        </h2>
        <div class="modal__actions">
          <a v-if="isTableCreation" class="modal__close" @click="hide()">
            <i class="iconoir-cancel"></i>
          </a>
        </div>
      </div>

      <div class="control">
        <label class="control__label">
          {{ $t('importFileModal.importLabel') }}
        </label>
        <div class="control__elements">
          <ul class="choice-items">
            <li v-if="isTableCreation">
              <a
                class="choice-items__link"
                :class="{ active: importer === '' }"
                @click=";[(importer = ''), reset()]"
              >
                <i class="choice-items__icon iconoir-copy"></i>
                <span>{{ $t('importFileModal.newTable') }}</span>
                <i
                  v-if="importer === ''"
                  class="choice-items__icon-active iconoir-check-circle"
                ></i>
              </a>
            </li>
            <li v-for="importerType in importerTypes" :key="importerType.type">
              <a
                class="choice-items__link"
                :class="{ active: importer === importerType.type }"
                @click=";[(importer = importerType.type), reset()]"
              >
                <i
                  class="choice-items__icon"
                  :class="importerType.iconClass"
                ></i>
                <span> {{ importerType.getName() }}</span>
                <i
                  v-if="importer === importerType.type"
                  class="choice-items__icon-active iconoir-check-circle"
                ></i>
              </a>
            </li>
          </ul>
        </div>
      </div>

      <TableForm
        ref="tableForm"
        :default-name="getDefaultName()"
        :creation="isTableCreation"
        @submitted="submitted"
      >
        <component
          :is="importerComponent"
          :disabled="importInProgress"
          @changed="reset()"
          @header="onHeader($event)"
          @data="onData($event)"
          @getData="onGetData($event)"
        />
      </TableForm>

      <Error :error="error"></Error>
      <Alert v-if="errorReport.length > 0 && error.visible" type="warning">
        <template #title>{{
          $t('importFileModal.reportTitleFailure')
        }}</template>

        {{ $t('importFileModal.reportMessage') }} {{ errorReport.join(', ') }}
      </Alert>
      <Alert v-if="errorReport.length > 0 && !error.visible" type="warning">
        <template #title>
          {{ $t('importFileModal.reportTitleSuccess') }}</template
        >

        {{ $t('importFileModal.reportMessage') }}
        {{ errorReport.join(', ') }}
      </Alert>

      <Tabs v-if="dataLoaded" :no-separation="true">
        <Tab
          v-if="!isTableCreation"
          :title="$t('importFileModal.importPreview')"
        >
          <SimpleGrid
            class="import-modal__preview"
            :rows="previewImportData"
            :fields="fields"
          />
        </Tab>
        <Tab :title="$t('importFileModal.filePreview')">
          <SimpleGrid
            class="import-modal__preview"
            :rows="previewFileData"
            :fields="fileFields"
          />
        </Tab>
      </Tabs>

      <div
        v-if="!jobHasSucceeded || errorReport.length === 0"
        class="modal-progress__actions"
      >
        <ProgressBar
          v-if="importInProgress && showProgressBar"
          :value="progressPercentage"
          :status="humanReadableState"
        />
        <div class="align-right">
          <button
            class="button button--large"
            :class="{
              'button--loading':
                importInProgress || (jobHasSucceeded && !isTableCreated),
            }"
            :disabled="
              importInProgress ||
              !canBeSubmitted ||
              (jobHasSucceeded && !isTableCreated)
            "
            @click="$refs.tableForm.submit()"
          >
            {{
              isTableCreation
                ? $t('importFileModal.addButton')
                : $t('importFileModal.importButton')
            }}
          </button>
        </div>
      </div>
      <div v-else class="align-right">
        <button
          class="button button--large button--success"
          :class="{ 'button--loading': !isTableCreated }"
          @click="openTable()"
        >
          {{
            isTableCreation
              ? $t('importFileModal.openCreatedTable')
              : $t('importFileModal.showTable')
          }}
        </button>
      </div>
    </template>
    <template v-if="!isTableCreation" #sidebar>
      <div class="import-modal__field-mapping">
        <div v-if="header.length > 0" class="import-modal__field-mapping-body">
          <h3>{{ $t('importFileModal.fieldMappingTitle') }}</h3>
          <p>{{ $t('importFileModal.fieldMappingDescription') }}</p>
          <div v-for="(head, index) in header" :key="head" class="control">
            <label class="control__label control__label--small">
              {{ head }}
            </label>
            <Dropdown v-model="mapping[index]">
              <DropdownItem name="Skip" :value="0" icon="ban" />
              <DropdownItem
                v-for="field in availableFields"
                :key="field.id"
                :name="field.name"
                :value="field.id"
                :icon="field._.type.iconClass"
                :disabled="
                  selectedFields.includes(field.id) &&
                  field.id !== mapping[index]
                "
              />
            </Dropdown>
          </div>
        </div>
        <div v-else class="import-modal__field-mapping--empty">
          <i class="import-modal__field-mapping-empty-icon iconoir-shuffle" />
          <div class="import-modal__field-mapping-empty-text">
            {{ $t('importFileModal.selectImportMessage') }}
          </div>
        </div>
      </div>
      <div class="modal__actions">
        <a class="modal__close" @click="hide()">
          <i class="iconoir-cancel"></i>
        </a>
      </div>
    </template>
  </Modal>
</template>

<script>
import VueRouter from 'vue-router'
import { clone } from '@baserow/modules/core/utils/object'
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import jobProgress from '@baserow/modules/core/mixins/jobProgress'
import TableService from '@baserow/modules/database/services/table'
import {
  uuid,
  getNextAvailableNameInSequence,
} from '@baserow/modules/core/utils/string'
import SimpleGrid from '@baserow/modules/database/components/view/grid/SimpleGrid'
import _ from 'lodash'

import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'

import TableForm from './TableForm'

export default {
  name: 'ImportFileModal',
  components: { TableForm, SimpleGrid },
  mixins: [modal, error, jobProgress],
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: false,
      default: null,
    },
    fields: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  data() {
    return {
      importer: '',
      uploadProgressPercentage: 0,
      importState: null,
      showProgressBar: false,
      header: [],
      mapping: {},
      getData: null,
      previewData: [],
      dataLoaded: false,
    }
  },
  computed: {
    isTableCreation() {
      return this.table === null
    },
    isTableCreated() {
      if (!this.job?.table_id) {
        return false
      }
      return this.database.tables.some(({ id }) => id === this.job.table_id)
    },
    canBeSubmitted() {
      return (
        this.isTableCreation ||
        (this.importer &&
          Object.values(this.mapping).some(
            (value) => this.fieldIndexMap[value] !== undefined
          ))
      )
    },
    fieldTypes() {
      return this.$registry.getAll('field')
    },
    fileFields() {
      return this.header.map((header, index) => ({
        type: 'text',
        name: header,
        id: uuid(),
        order: index,
      }))
    },
    /**
     * All writable fields.
     */
    writableFields() {
      return this.fields.filter(
        ({ type }) => !this.fieldTypes[type].getIsReadOnly()
      )
    },
    /**
     * Map beetween the field id and its index in the array.
     */
    fieldIndexMap() {
      return Object.fromEntries(
        this.writableFields.map((field, index) => [field.id, index])
      )
    },
    /**
     * All writable fields that can be imported into
     */
    availableFields() {
      return this.writableFields.filter(({ type }) =>
        this.fieldTypes[type].getCanImport()
      )
    },
    fieldMapping() {
      return Object.entries(this.mapping)
        .filter(
          ([, targetFieldId]) =>
            !!targetFieldId ||
            // Check if we have an id from a removed field
            this.fieldIndexMap[targetFieldId] !== undefined
        )
        .map(([importIndex, targetFieldId]) => {
          return [importIndex, this.fieldIndexMap[targetFieldId]]
        })
    },
    // Template row with default values
    defaultRow() {
      return this.writableFields.map((field) =>
        this.fieldTypes[field.type].getEmptyValue(field)
      )
    },
    previewFileData() {
      return this.previewData.map((row) => {
        const newRow = Object.fromEntries(
          this.fileFields.map((field, index) => [
            `field_${field.id}`,
            `${row[index]}`,
          ])
        )
        newRow.id = uuid()
        return newRow
      })
    },
    previewImportData() {
      return this.previewData.map((row) => {
        const newRow = Object.fromEntries(
          this.fieldMapping.map(([importIndex, fieldIndex]) => {
            const field = this.writableFields[fieldIndex]
            return [
              `field_${field.id}`,
              this.fieldTypes[field.type].prepareValueForPaste(
                field,
                `${row[importIndex]}`,
                row[importIndex]
              ),
            ]
          })
        )
        newRow.id = uuid()
        return newRow
      })
    },

    /**
     * Fields that are mapped to a column
     */
    selectedFields() {
      return Object.values(this.mapping)
    },
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
          return this.$t('importFileModal.preparing')
        case 'uploading':
          if (this.uploadProgressPercentage === 100) {
            return this.$t('job.statePending')
          } else {
            return this.$t('importFileModal.uploading')
          }
        default:
          return this.jobHumanReadableState
      }
    },
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
  beforeDestroy() {
    this.stopPollIfRunning()
  },
  methods: {
    getDefaultName() {
      const excludeNames = this.database.tables.map((table) => table.name)
      const baseName = this.$t('importFileModal.defaultName')
      return getNextAvailableNameInSequence(baseName, excludeNames)
    },
    reset(full = true) {
      this.job = null
      this.uploadProgressPercentage = 0
      if (full) {
        this.header = []
        this.importState = null
        this.mapping = {}
        this.getData = null
        this.previewData = []
        this.dataLoaded = false
      }
      this.hideError()
    },
    onData({ header, previewData }) {
      this.header = header
      this.previewData = previewData
      this.mapping = Object.fromEntries(
        header.map((name, index) => {
          const foundField = this.availableFields.find(
            ({ name: fieldName }) => fieldName === name
          )
          return [index, foundField ? foundField.id : 0]
        })
      )
      this.dataLoaded = header.length > 0 || previewData.length > 0
    },
    onGetData(getData) {
      this.getData = getData
    },
    onHeader(header) {
      this.header = header
      this.mapping = Object.fromEntries(
        header.map((name, index) => {
          const foundField = this.availableFields.find(
            ({ name: fieldName }) => fieldName === name
          )
          return [index, foundField ? foundField.id : 0]
        })
      )
    },
    /**
     * When the form is submitted we try to extract the initial data and first row
     * header setting from the values. An importer could have added those, but they
     * need to be removed from the values.
     */
    async submitted(formValues) {
      this.showProgressBar = false
      this.reset(false)
      let data = null
      const values = { ...formValues }

      if (typeof this.getData === 'function') {
        try {
          this.showProgressBar = true
          this.importState = 'preparingData'
          await this.$ensureRender()

          data = await this.getData()

          if (!this.isTableCreation) {
            const fieldMapping = Object.entries(this.mapping)
              .filter(
                ([, targetFieldId]) =>
                  !!targetFieldId ||
                  // Check if we have an id from a removed field
                  this.fieldIndexMap[targetFieldId] !== undefined
              )
              .map(([importIndex, targetFieldId]) => {
                return [importIndex, this.fieldIndexMap[targetFieldId]]
              })

            // Template row with default values
            const defaultRow = this.writableFields.map((field) =>
              this.fieldTypes[field.type].getEmptyValue(field)
            )

            // Precompute the prepare value function for each field
            const prepareValueByField = this.writableFields.map(
              (field) => (value) =>
                this.fieldTypes[field.type].prepareValueForUpdate(
                  field,
                  this.fieldTypes[field.type].prepareValueForPaste(
                    field,
                    `${value}`,
                    value
                  )
                )
            )

            // Processes the data by chunk to avoid UI freezes
            const result = []
            for (const chunk of _.chunk(data, 1000)) {
              result.push(
                chunk.map((row) => {
                  const newRow = clone(defaultRow)
                  fieldMapping.forEach(([importIndex, targetIndex]) => {
                    newRow[targetIndex] = prepareValueByField[targetIndex](
                      row[importIndex]
                    )
                  })

                  return newRow
                })
              )
              await this.$ensureRender()
            }
            data = result.flat()
          } else {
            // Add the header in case of table creation
            data = [this.header, ...data]
          }
        } catch (error) {
          this.reset()
          this.handleError(error, 'application')
        }
      }

      this.importState = 'uploading'

      const onUploadProgress = ({ loaded, total }) =>
        (this.uploadProgressPercentage = (loaded / total) * 100)

      try {
        if (data && data.length > 0) {
          this.showProgressBar = true
        }

        if (this.isTableCreation) {
          const { data: job } = await TableService(this.$client).create(
            this.database.id,
            values,
            data,
            true,
            {
              onUploadProgress,
            }
          )
          this.startJobPoller(job)
        } else {
          const { data: job } = await TableService(this.$client).importData(
            this.table.id,
            data,
            {
              onUploadProgress,
            }
          )
          this.startJobPoller(job)
        }
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
        'row-import-creation': this.$t('importFileModal.stateRowCreation'),
        'row-import-validation': this.$t('importFileModal.statePreValidation'),
        'import-create-table': this.$t('importFileModal.stateCreateTable'),
      }
      return translations[jobState]
    },
    async openTable() {
      // Redirect to the newly created table.
      try {
        await this.$nuxt.$router.push({
          name: 'database-table',
          params: {
            databaseId: this.database.id,
            tableId: this.job.table_id,
          },
        })
      } catch (error) {
        // When redirecting to the `database-table`, it can happen that it redirects
        // to another view. For some reason, this is causing the router throw an
        // error. In our case, it's perfectly fine, so we're suppressing this error
        // here. More information:
        // https://stackoverflow.com/questions/62223195/vue-router-uncaught-in-promise-
        // error-redirected-from-login-to-via-a
        const { isNavigationFailure, NavigationFailureType } = VueRouter
        if (!isNavigationFailure(error, NavigationFailureType.redirected)) {
          throw error
        }
      }
      this.hide()
    },
    async onJobDone() {
      if (this.isTableCreation) {
        // Let's add the table to the store...
        const { data: table } = await TableService(this.$client).get(
          this.job.table_id
        )

        await this.$store.dispatch('table/forceUpsert', {
          database: this.database,
          data: table,
        })

        if (this.errorReport.length === 0) {
          await this.openTable()
        }
      } else {
        this.$bus.$emit('table-refresh', {
          tableId: this.job.table_id,
        })
        if (this.errorReport.length === 0) {
          this.hide()
        }
      }
    },
    onJobFailed() {
      const error = new ResponseErrorMessage(
        this.$t('importFileModal.importError'),
        this.job.human_readable_error
      )
      this.stopPollAndHandleError(error)
    },
    onJobPollingError(error) {
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
