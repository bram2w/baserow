<template>
  <div>
    <div class="control">
      <label class="control__label">{{
        $t('tableCSVImporter.chooseFileLabel')
      }}</label>
      <div class="control__description">
        {{ $t('tableCSVImporter.chooseFileDescription') }}
      </div>
      <div class="control__elements">
        <div class="file-upload">
          <input
            v-show="false"
            ref="file"
            type="file"
            accept=".csv"
            @change="select($event)"
          />
          <a
            class="button button--large button--ghost file-upload__button"
            :class="{ 'button--loading': state !== null }"
            :disabled="disabled"
            @click.prevent="!disabled && $refs.file.click($event)"
          >
            <i class="fas fa-cloud-upload-alt"></i>
            {{ $t('tableCSVImporter.chooseFile') }}
          </a>
          <div v-if="state === null" class="file-upload__file">
            {{ filename }}
          </div>
          <template v-else>
            <ProgressBar
              :value="fileLoadingProgress"
              :show-value="state === 'loading'"
              :status="
                state === 'loading' ? $t('importer.loading') : stateTitle
              "
            />
          </template>
        </div>
        <div v-if="$v.filename.$error" class="error">
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </div>
    <div v-if="filename !== ''" class="row">
      <div class="col col-4">
        <div class="control">
          <label class="control__label">{{
            $t('tableCSVImporter.columnSeparator')
          }}</label>
          <div class="control__elements">
            <Dropdown
              v-model="columnSeparator"
              :disabled="isDisabled"
              @input="reload()"
            >
              <DropdownItem name="auto detect" value="auto"></DropdownItem>
              <DropdownItem name="," value=","></DropdownItem>
              <DropdownItem name=";" value=";"></DropdownItem>
              <DropdownItem name="|" value="|"></DropdownItem>
              <DropdownItem name="<tab>" value="\t"></DropdownItem>
              <DropdownItem
                :name="$t('tableCSVImporter.recordSeparator') + ' (30)'"
                :value="String.fromCharCode(30)"
              ></DropdownItem>
              <DropdownItem
                :name="$t('tableCSVImporter.unitSeparator') + ' (31)'"
                :value="String.fromCharCode(31)"
              ></DropdownItem>
            </Dropdown>
          </div>
        </div>
      </div>
      <div class="col col-8">
        <div class="control">
          <label class="control__label">{{
            $t('tableCSVImporter.encoding')
          }}</label>
          <div class="control__elements">
            <CharsetDropdown
              v-model="encoding"
              :disabled="isDisabled"
              @input="reload()"
            ></CharsetDropdown>
          </div>
        </div>
      </div>
    </div>
    <div v-if="filename !== ''" class="row">
      <div class="col col-6">
        <div class="control">
          <label class="control__label">{{
            $t('tableCSVImporter.firstRowHeader')
          }}</label>
          <div class="control__elements">
            <Checkbox
              v-model="values.firstRowHeader"
              :disabled="isDisabled"
              @input="reloadPreview()"
              >{{ $t('common.yes') }}</Checkbox
            >
          </div>
        </div>
      </div>
    </div>
    <Alert
      v-if="error !== ''"
      :title="$t('common.wrong')"
      type="error"
      icon="exclamation"
    >
      {{ error }}
    </Alert>
    <TableImporterPreview
      v-if="error === '' && Object.keys(preview).length !== 0"
      :preview="preview"
    ></TableImporterPreview>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import CharsetDropdown from '@baserow/modules/core/components/helpers/CharsetDropdown'
import importer from '@baserow/modules/database/mixins/importer'
import TableImporterPreview from '@baserow/modules/database/components/table/TableImporterPreview'

export default {
  name: 'TableCSVImporter',
  components: { TableImporterPreview, CharsetDropdown },
  mixins: [form, importer],
  data() {
    return {
      values: {
        data: null,
        firstRowHeader: true,
        getData: null,
      },
      filename: '',
      columnSeparator: 'auto',
      encoding: 'utf-8',
      error: '',
      rawData: null,
      preview: {},
    }
  },
  validations: {
    values: {
      getData: { required },
    },
    filename: { required },
  },
  computed: {
    isDisabled() {
      return this.disabled || this.state !== null
    },
  },
  methods: {
    /**
     * Method that is called when a file has been chosen. It will check if the file is
     * not larger than 15MB. Otherwise it will take a long time and possibly a crash
     * if so many entries have to be loaded into memory. If the file is valid, the
     * contents will be loaded into memory and the reload method will be called which
     * parses the content.
     */
    select(event) {
      if (event.target.files.length === 0) {
        return
      }

      const file = event.target.files[0]
      const maxSize =
        parseInt(this.$env.BASEROW_MAX_IMPORT_FILE_SIZE_MB, 10) * 1024 * 1024

      this.fileLoadingProgress = 0

      if (file.size > maxSize) {
        this.filename = ''
        this.values.data = null
        this.values.getData = null
        this.error = this.$t('tableCSVImporter.limitFileSize', {
          limit: this.$env.BASEROW_MAX_IMPORT_FILE_SIZE_MB,
        })
        this.preview = {}
      } else {
        this.$emit('changed')
        this.filename = file.name
        this.state = 'loading'
        const reader = new FileReader()
        reader.addEventListener('progress', (event) => {
          this.fileLoadingProgress = (event.loaded / event.total) * 100
        })
        reader.addEventListener('load', (event) => {
          this.rawData = event.target.result
          this.fileLoadingProgress = 100
          this.reload()
        })
        reader.readAsArrayBuffer(event.target.files[0])
      }
    },
    /**
     * Parses the raw data with the user configured delimiter. If all looks good the
     * data is stored as a string because all the entries don't have to be reactive.
     * Also a small preview will be generated. If something goes wrong, for example
     * when the CSV doesn't have any entries the appropriate error will be shown.
     */
    async reload() {
      this.state = 'parsing'
      await this.$ensureRender()

      const decoder = new TextDecoder(this.encoding)
      const decodedData = decoder.decode(this.rawData)
      const limit = this.$env.INITIAL_TABLE_DATA_LIMIT
      const count = decodedData.split(/\r\n|\r|\n/).length
      if (limit !== null && count > limit) {
        this.values.data = null
        this.values.getData = null
        this.error = this.$t('tableCSVImporter.limitError', {
          limit,
        })
        this.preview = {}
        return
      }

      await this.$ensureRender()
      // Parse only the first 4 rows to show a preview. (header + 3 rows)
      this.$papa.parse(decodedData, {
        preview: 4,
        dynamicTyping: true,
        skipEmptyLines: true,
        delimiter: this.columnSeparator === 'auto' ? '' : this.columnSeparator,
        complete: (data) => {
          if (data.data.length === 0) {
            // We need at least a single entry otherwise the user has probably chosen
            // a wrong file.
            this.values.data = null
            this.values.getData = null
            this.error = this.$t('tableCSVImporter.emptyCSV')
            this.preview = {}
          } else {
            // Store the data to reload the preview without reparsing.
            this.values.data = [...data.data]
            // If parsed successfully and it is not empty then the initial data can be
            // prepared for creating the table.
            const dataWithHeader = this.ensureHeaderExistsAndIsValid(
              data.data,
              this.values.firstRowHeader
            )
            // If the first row is not the header, remove the last row as we will
            // be adding one row of generated headers.
            if (!this.values.firstRowHeader) dataWithHeader.pop()
            this.error = ''
            this.preview = this.getPreview(dataWithHeader)
            this.state = null
            this.parsing = false
          }
        },
        error(error) {
          // Papa parse has resulted in an error which we need to display to the user.
          // All previously loaded data will be removed.
          this.values.data = null
          this.values.getData = null
          this.error = error.errors[0].message
          this.preview = {}
          this.state = null
          this.parsing = false
          this.fileLoadingProgress = 0
        },
      })

      // Prepare a callback function to be called when the form is submitted.
      // This is where the rest of the parsing takes place.
      // This was added to avoid the UI freezing while uploading large files.
      const getData = () => {
        return new Promise((resolve, reject) => {
          this.$ensureRender().then(() => {
            this.$papa.parse(decodedData, {
              dynamicTyping: true,
              skipEmptyLines: true,
              delimiter:
                this.columnSeparator === 'auto' ? '' : this.columnSeparator,
              complete: async (data) => {
                if (this.values.firstRowHeader) {
                  // Only run ensureHeaderExistsAndIsValid on the first row
                  // as it can't handle too many rows.
                  const dataWithHeader = this.ensureHeaderExistsAndIsValid(
                    data.data.slice(0, 1),
                    this.values.firstRowHeader
                  )
                  // Update the header row with the valid header names
                  data.data[0] = dataWithHeader[0]
                }
                await this.$ensureRender()
                resolve(data.data)
              },
              error(error) {
                reject(error)
              },
            })
          })
        })
      }

      if (this.error === '') {
        this.values.getData = getData
      } else {
        this.values.getData = null
      }
    },
    /**
     * Reload the preview without re-parsing the raw data.
     */
    reloadPreview() {
      const rows = [...this.values.data]
      if (!this.values.firstRowHeader) rows.pop()
      const dataWithHeader = this.ensureHeaderExistsAndIsValid(
        rows,
        this.values.firstRowHeader
      )
      this.preview = this.getPreview(dataWithHeader)
    },
  },
}
</script>
