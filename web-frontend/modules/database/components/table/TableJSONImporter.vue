<template>
  <div>
    <div class="control">
      <label class="control__label">Choose JSON file</label>
      <div class="control__description">
        You can import an existing JSON file by uploading the .json file with
        tabular data, i.e.:
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
            Choose JSON file
          </a>
          <div class="file-upload__file">{{ filename }}</div>
        </div>
        <div v-if="$v.filename.$error" class="error">
          This field is required.
        </div>
      </div>
    </div>
    <div v-if="filename !== ''" class="control">
      <label class="control__label">Encoding</label>
      <div class="control__elements">
        <CharsetDropdown v-model="encoding" @input="reload()"></CharsetDropdown>
      </div>
    </div>
    <div v-if="error !== ''" class="alert alert--error alert--has-icon">
      <div class="alert__icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert__title">Something went wrong</div>
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
        this.error = 'The maximum file size is 15MB.'
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
        this.error = `Error occured while parsing JSON: ${error.message}`
        this.preview = {}
        return
      }

      if (json.length === 0) {
        this.values.data = ''
        this.error = 'This JSON file is empty.'
        this.preview = {}
        return
      }

      if (!Array.isArray(json)) {
        this.values.data = ''
        this.error = `The JSON file is not an array.`
        this.preview = {}
        return
      }

      const limit = this.$env.INITIAL_TABLE_DATA_LIMIT
      if (limit !== null && json.length > limit - 1) {
        this.values.data = ''
        this.error = `It is not possible to import more than ${limit} rows.`
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

      this.values.data = JSON.stringify(data)
      this.error = ''
      this.preview = this.getPreview(data, true)
    },
  },
}
</script>
