<template>
  <div>
    <div class="control">
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
        </pre>
      </div>
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
            @click.prevent="$refs.file.click($event)"
          >
            <i class="fas fa-cloud-upload-alt"></i>
            {{ $t('tableJSONImporter.chooseButton') }}
          </a>
          <div class="file-upload__file">{{ filename }}</div>
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
        <CharsetDropdown v-model="encoding" @input="reload()"></CharsetDropdown>
      </div>
    </div>
    <div v-if="error !== ''" class="alert alert--error alert--has-icon">
      <div class="alert__icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert__title">{{ $t('common.wrong') }}</div>
      <p class="alert__content">
        {{ error }}
      </p>
    </div>
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
        data: '',
        firstRowHeader: true,
      },
      encoding: 'utf-8',
      filename: '',
      error: '',
      rawData: null,
      preview: {},
    }
  },
  validations: {
    values: {
      data: { required },
    },
    filename: { required },
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
      const maxSize = 1024 * 1024 * 15

      if (file.size > maxSize) {
        this.filename = ''
        this.values.data = ''
        this.error = this.$t('tableJSONImporter.limitFileSize', {
          limit: 15,
        })
        this.preview = {}
        this.$emit('input', this.value)
      } else {
        this.filename = file.name
        const reader = new FileReader()
        reader.addEventListener('load', (event) => {
          this.rawData = event.target.result
          this.reload()
        })
        reader.readAsArrayBuffer(event.target.files[0])
      }
    },
    reload() {
      let json

      try {
        const decoder = new TextDecoder(this.encoding)
        const decoded = decoder.decode(this.rawData)
        json = JSON.parse(decoded)
      } catch (error) {
        this.values.data = ''
        this.error = this.$t('tableJSONImporter.processingError', {
          error: error.message,
        })
        this.preview = {}
        return
      }

      if (json.length === 0) {
        this.values.data = ''
        this.error = this.$t('tableJSONImporter.emptyError')
        this.preview = {}
        return
      }

      if (!Array.isArray(json)) {
        this.values.data = ''
        this.error = this.$t('tableJSONImporter.arrayError')
        this.preview = {}
        return
      }

      const limit = this.$env.INITIAL_TABLE_DATA_LIMIT
      if (limit !== null && json.length > limit - 1) {
        this.values.data = ''
        this.error = this.error = this.$t('tableJSONImporter.limitError', {
          limit,
        })
        this.preview = {}
        return
      }

      const header = []
      const data = []

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
          const value = exists ? entry[key].toString() : ''
          row.push(value)
        })

        data.push(row)
      })

      data.unshift(header)

      const dataWithHeader = this.ensureHeaderExistsAndIsValid(data, true)
      this.values.data = JSON.stringify(dataWithHeader)
      this.error = ''
      this.preview = this.getPreview(dataWithHeader)
    },
  },
}
</script>

<i18n>
{
  "en": {
    "tableJSONImporter": {
      "fileLabel": "Choose JSON file",
      "fileDescription": "You can import an existing JSON file by uploading the .json file with tabular data, i.e.:",
      "chooseButton": "Choose JSON file",
      "encodingLabel": "Encoding",
      "processingError": "Error occurred while parsing JSON: {error}",
      "arrayError": "The JSON file is not an array.",
      "emptyError": "This JSON file is empty.",
      "limitFileSize": "The maximum file size is {limit}MB.",
      "limitError": "It is not possible to import more than {limit} rows."
    }
  },
  "fr": {
    "tableJSONImporter": {
      "fileLabel": "Choisissez un fichier JSON",
      "fileDescription": "Vous pouvez importer un JSON existant en envoyant un fichier .json contenant des données tabulaires, c'est-à-dire :",
      "chooseButton": "Choisir un fichier JSON",
      "encodingLabel": "Encodage",
      "processingError": "Une erreur est survenue lors du traitement du JSON : {error}",
      "arrayError": "Ce fichier JSON n'est pas un tableau.",
      "emptyError": "Ce fichier JSON est vide.",
      "limitFileSize": "La taille maximum de fichier est de {limit}Mo.",
      "limitError": "Il n'est pas possible d'importer plus de {limit} lignes."
    }
  }
}
</i18n>
