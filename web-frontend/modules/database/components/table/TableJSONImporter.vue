<template>
  <div>
    <div class="control">
      <template v-if="filename === ''">
        <label class="control__label">{{
          $t('tableJSONImporter.fileLabel')
        }}</label>
        <div class="control__description">
          {{ $t('tableJSONImporter.fileDescription') }}
          <pre>
[
  {
    "to": "Tove",
    "from": "Jani",
    "heading": "Reminder",
    "body": "Don't forget me this weekend!"
  },
  {
    "to": "Bram",
    "from": "Nigel",
    "heading": "Reminder",
    "body": "Don't forget about the export feature this week"
  }
]
        </pre
          >
        </div>
      </template>
      <div class="control__elements">
        <div class="file-upload">
          <input
            v-show="false"
            ref="file"
            type="file"
            accept=".json"
            @change="select($event)"
          />
          <a
            class="button button--large button--ghost file-upload__button"
            :class="{ 'button--loading': state !== null }"
            @click.prevent="$refs.file.click($event)"
          >
            <i class="fas fa-cloud-upload-alt"></i>
            {{ $t('tableJSONImporter.chooseButton') }}
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
          {{ $t('error.fieldRequired') }}
        </div>
      </div>
    </div>
    <div v-if="filename !== ''" class="control">
      <label class="control__label">{{
        $t('tableJSONImporter.encodingLabel')
      }}</label>
      <div class="control__elements">
        <CharsetDropdown
          v-model="encoding"
          :disabled="isDisabled"
          @input="reload()"
        ></CharsetDropdown>
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
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import CharsetDropdown from '@baserow/modules/core/components/helpers/CharsetDropdown'
import importer from '@baserow/modules/database/mixins/importer'

export default {
  name: 'TableCSVImporter',
  components: { CharsetDropdown },
  mixins: [form, importer],
  data() {
    return {
      encoding: 'utf-8',
      filename: '',
      rawData: null,
    }
  },
  validations: {
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

      if (file.size > maxSize) {
        this.filename = ''
        this.handleImporterError(
          this.$t('tableJSONImporter.limitFileSize', {
            limit: this.$env.BASEROW_MAX_IMPORT_FILE_SIZE_MB,
          })
        )
      } else {
        this.state = 'loading'
        this.$emit('changed')
        this.filename = file.name
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
    async reload() {
      let json
      this.resetImporterState()

      try {
        const decoder = new TextDecoder(this.encoding)
        this.state = 'parsing'
        await this.$ensureRender()
        const decoded = decoder.decode(this.rawData)

        await this.$ensureRender()
        json = JSON.parse(decoded)
      } catch (error) {
        this.handleImporterError(
          this.$t('tableJSONImporter.processingError', {
            error: error.message,
          })
        )
        return
      }

      if (json.length === 0) {
        this.handleImporterError(this.$t('tableJSONImporter.emptyError'))
        return
      }

      if (!Array.isArray(json)) {
        this.handleImporterError(this.$t('tableJSONImporter.arrayError'))
        return
      }

      const limit = this.$env.INITIAL_TABLE_DATA_LIMIT
      if (limit !== null && json.length > limit - 1) {
        this.handleImporterError(
          this.$t('tableJSONImporter.limitError', {
            limit,
          })
        )
        return
      }

      const header = []
      const data = []

      await this.$ensureRender()

      json.forEach((entry) => {
        const keys = Object.keys(entry)
        const row = []

        keys.forEach((key) => {
          if (!header.includes(key)) {
            header.push(key)
          }
        })

        header.forEach((key) => {
          const exists = Object.prototype.hasOwnProperty.call(entry, key)
          const value = exists ? entry[key] : ''
          row.push(value)
        })

        data.push(row)
      })

      const preparedHeader = this.prepareHeader(header, data)
      const getData = () => {
        return data
      }
      this.state = null
      const previewData = this.getPreview(header, data)

      this.$emit('getData', getData)
      this.$emit('data', { header: preparedHeader, previewData })
    },
  },
}
</script>
