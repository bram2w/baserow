<template>
  <div>
    <div class="control">
      <label class="control__label">Choose CSV file</label>
      <div class="control__description">
        You can import an existing CSV by uploading the .CSV file with tabular
        data. Most spreadsheet applications will allow you to export your
        spreadsheet as a .CSV file.
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
            @click.prevent="$refs.file.click($event)"
          >
            <i class="fas fa-cloud-upload-alt"></i>
            Choose CSV file
          </a>
          <div class="file-upload__file">{{ filename }}</div>
        </div>
        <div v-if="$v.filename.$error" class="error">
          This field is required.
        </div>
      </div>
    </div>
    <div v-if="filename !== ''" class="row">
      <div class="col col-4">
        <div class="control">
          <label class="control__label">Column separator</label>
          <div class="control__elements">
            <Dropdown v-model="columnSeparator" @input="reload()">
              <DropdownItem name="auto detect" value="auto"></DropdownItem>
              <DropdownItem name="," value=","></DropdownItem>
              <DropdownItem name=";" value=";"></DropdownItem>
              <DropdownItem name="|" value="|"></DropdownItem>
              <DropdownItem name="<tab>" value="\t"></DropdownItem>
              <DropdownItem
                name="record separator (30)"
                :value="String.fromCharCode(30)"
              ></DropdownItem>
              <DropdownItem
                name="unit separator (31)"
                :value="String.fromCharCode(31)"
              ></DropdownItem>
            </Dropdown>
          </div>
        </div>
      </div>
      <div class="col col-8">
        <div class="control">
          <label class="control__label">Encoding</label>
          <div class="control__elements">
            <Dropdown v-model="encoding" @input="reload()">
              <DropdownItem name="Unicode (UTF-8)" value="utf-8"></DropdownItem>
              <DropdownItem
                name="Arabic (ISO-8859-6)"
                value="iso-8859-6"
              ></DropdownItem>
              <DropdownItem
                name="Arabic (Windows-1256)"
                value="windows-1256"
              ></DropdownItem>
              <DropdownItem
                name="Baltic (ISO-8859-4)"
                value="iso-8859-4"
              ></DropdownItem>
              <DropdownItem
                name="Baltic (windows-1257)"
                value="windows-1257"
              ></DropdownItem>
              <DropdownItem
                name="Celtic (ISO-8859-14)"
                value="iso-8859-14"
              ></DropdownItem>
              <DropdownItem
                name="Central European (ISO-8859-2)"
                value="iso-8859-2"
              ></DropdownItem>
              <DropdownItem
                name="Central European (Windows-1250)"
                value="windows-1250"
              ></DropdownItem>
              <DropdownItem
                name="Chinese, Simplified (GBK)"
                value="gbk"
              ></DropdownItem>
              <DropdownItem
                name="Chinese (GB18030)"
                value="gb18030"
              ></DropdownItem>
              <DropdownItem
                name="Chinese Traditional (Big5)"
                value="big5"
              ></DropdownItem>
              <DropdownItem
                name="Cyrillic (KOI8-R)"
                value="koi8-r"
              ></DropdownItem>
              <DropdownItem
                name="Cyrillic (KOI8-U)"
                value="koi8-u"
              ></DropdownItem>
              <DropdownItem
                name="Cyrillic (ISO-8859-5)"
                value="iso-8859-5"
              ></DropdownItem>
              <DropdownItem
                name="Cyrillic (Windows-1251)"
                value="windows-1251"
              ></DropdownItem>
              <DropdownItem
                name="Cyrillic Mac OS (x-mac-cyrillic)"
                value="x-mac-cyrillic"
              ></DropdownItem>
              <DropdownItem
                name="Greek (ISO-8859-7)"
                value="iso-8859-7"
              ></DropdownItem>
              <DropdownItem
                name="Greek (Windows-1253)"
                value="windows-1253"
              ></DropdownItem>
              <DropdownItem
                name="Hebrew (ISO-8859-8)"
                value="iso-8859-8"
              ></DropdownItem>
              <DropdownItem
                name="Hebrew (Windows-1255)"
                value="windows-1255"
              ></DropdownItem>
              <DropdownItem
                name="Japanese (EUC-JP)"
                value="euc-jp"
              ></DropdownItem>
              <DropdownItem
                name="Japanese (ISO-2022-JP)"
                value="iso-2022-jp"
              ></DropdownItem>
              <DropdownItem
                name="Japanese (Shift-JIS)"
                value="shift-jis"
              ></DropdownItem>
              <DropdownItem
                name="Korean (EUC-KR)"
                value="euc-kr"
              ></DropdownItem>
              <DropdownItem name="Macintosh" value="macintosh"></DropdownItem>
              <DropdownItem
                name="Nordic (ISO-8859-10)"
                value="iso-8859-10"
              ></DropdownItem>
              <DropdownItem
                name="South-Eastern European (ISO-8859-16)"
                value="iso-8859-16"
              ></DropdownItem>
              <DropdownItem
                name="Thai (Windows-874)"
                value="windows-874"
              ></DropdownItem>
              <DropdownItem
                name="Turkish (Windows-1254)"
                value="windows-1254"
              ></DropdownItem>
              <DropdownItem
                name="Vietnamese (Windows-1258)"
                value="windows-1258"
              ></DropdownItem>
              <DropdownItem
                name="Western European (ISO-8859-1)"
                value="iso-8859-1"
              ></DropdownItem>
              <DropdownItem
                name="Western European (Windows-1252)"
                value="windows-1252"
              ></DropdownItem>
              <DropdownItem
                name="Latin 3 (ISO-8859-3)"
                value="iso-8859-3"
              ></DropdownItem>
            </Dropdown>
          </div>
        </div>
      </div>
    </div>
    <div v-if="filename !== ''" class="row">
      <div class="col col-6">
        <div class="control">
          <label class="control__label">First row is header</label>
          <div class="control__elements">
            <Checkbox v-model="values.firstRowHeader" @input="reload()"
              >yes</Checkbox
            >
          </div>
        </div>
      </div>
    </div>
    <div
      v-if="error !== ''"
      class="alert alert--error alert--has-icon margin-top-1"
    >
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
import Papa from 'papaparse'
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import importer from '@baserow/modules/database/mixins/importer'
import TableImporterPreview from '@baserow/modules/database/components/table/TableImporterPreview'

export default {
  name: 'TableCSVImporter',
  components: { TableImporterPreview },
  mixins: [form, importer],
  data() {
    return {
      values: {
        data: '',
        firstRowHeader: true,
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
    /**
     * Parses the raw data with the user configured delimiter. If all looks good the
     * data is stored as a string because all the entries don't have to be reactive.
     * Also a small preview will be generated. If something goes wrong, for example
     * when the CSV doesn't have any entries the appropriate error will be shown.
     */
    reload() {
      const decoder = new TextDecoder(this.encoding)
      const decodedData = decoder.decode(this.rawData)
      const limit = this.$env.INITIAL_TABLE_DATA_LIMIT
      const count = decodedData.split(/\r\n|\r|\n/).length
      if (limit !== null && count > limit) {
        this.values.data = ''
        this.error = `It is not possible to import more than ${limit} rows.`
        this.preview = {}
        this.$emit('input', this.value)
        return
      }

      Papa.parse(decodedData, {
        delimiter: this.columnSeparator === 'auto' ? '' : this.columnSeparator,
        complete: (data) => {
          if (data.data.length === 0) {
            // We need at least a single entry otherwise the user has probably chosen
            // a wrong file.
            this.values.data = ''
            this.error = 'This CSV file is empty.'
            this.preview = {}
          } else {
            // If parsed successfully and it is not empty then the initial data can be
            // prepared for creating the table. We store the data stringified because
            // it doesn't need to be reactive.
            this.values.data = JSON.stringify(data.data)
            this.error = ''
            this.preview = this.getPreview(
              data.data,
              this.values.firstRowHeader
            )
          }

          this.$emit('input', this.value)
        },
        error(error) {
          // Papa parse has resulted in an error which we need to display to the user.
          // All previously loaded data will be removed.
          this.values.data = ''
          this.error = error.errors[0].message
          this.preview = {}
          this.$emit('input', this.value)
        },
      })
    },
  },
}
</script>
