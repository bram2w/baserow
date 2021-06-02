<template>
  <div>
    <div class="control">
      <label class="control__label">Choose XML file</label>
      <div class="control__description">
        You can import an existing XML by uploading the .XML file with tabular
        data, i.e.:
        <pre>
&lt;notes&gt;
  &lt;note&gt;
    &lt;to&gt;Tove&lt;/to&gt;
    &lt;from&gt;Jani&lt;/from&gt;
    &lt;heading&gt;Reminder&lt;/heading&gt;
    &lt;body&gt;Don't forget me this weekend!&lt;/body&gt;
  &lt;/note&gt;
  &lt;note&gt;
    &lt;heading&gt;Reminder&lt;/heading&gt;
    &lt;heading2&gt;Reminder2&lt;/heading2&gt;
    &lt;to&gt;Tove&lt;/to&gt;
    &lt;from&gt;Jani&lt;/from&gt;
    &lt;body&gt;Don't forget me this weekend!&lt;/body&gt;
  &lt;/note&gt;
&lt;/notes&gt;</pre
        >
      </div>
      <div class="control__elements">
        <div class="file-upload">
          <input
            v-show="false"
            ref="file"
            type="file"
            accept=".xml"
            @change="select($event)"
          />
          <a
            class="button button--large button--ghost file-upload__button"
            @click.prevent="$refs.file.click($event)"
          >
            <i class="fas fa-cloud-upload-alt"></i>
            Choose XML file
          </a>
          <div class="file-upload__file">{{ filename }}</div>
        </div>
        <div v-if="$v.filename.$error" class="error">
          This field is required.
        </div>
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
import importer from '@baserow/modules/database/mixins/importer'
import TableImporterPreview from '@baserow/modules/database/components/table/TableImporterPreview'
import { parseXML } from '@baserow/modules/database/utils/xml'

export default {
  name: 'TableXMLImporter',
  components: { TableImporterPreview },
  mixins: [form, importer],
  data() {
    return {
      values: {
        data: '',
        firstRowHeader: true,
      },
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
      } else {
        this.filename = file.name
        const reader = new FileReader()
        reader.addEventListener('load', (event) => {
          this.rawData = event.target.result
          this.reload()
        })
        reader.readAsBinaryString(event.target.files[0])
      }
    },
    reload() {
      const [header, xmlData, errors] = parseXML(this.rawData)

      if (errors.length > 0) {
        this.values.data = ''
        this.error = `Error occured while processing XML: ${errors.join('\n')}`
        this.preview = {}
        return
      }

      if (xmlData.length === 0) {
        this.values.data = ''
        this.error = 'This XML file is empty.'
        this.preview = {}
        return
      }

      let hasHeader = false
      if (header.length > 0) {
        xmlData.unshift(header)
        hasHeader = true
      }

      const limit = this.$env.INITIAL_TABLE_DATA_LIMIT
      if (limit !== null && xmlData.length > limit) {
        this.values.data = ''
        this.error = `It is not possible to import more than ${limit} rows.`
        this.preview = {}
        return
      }

      this.values.data = JSON.stringify(xmlData)
      this.error = ''
      this.preview = this.getPreview(xmlData, hasHeader)
    },
  },
}
</script>
