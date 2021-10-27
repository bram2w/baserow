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
            @click.prevent="$refs.file.click($event)"
          >
            <i class="fas fa-cloud-upload-alt"></i>
            {{ $t('tableCSVImporter.chooseFile') }}
          </a>
          <div class="file-upload__file">{{ filename }}</div>
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
            <Dropdown v-model="columnSeparator" @input="reload()">
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
            <Checkbox v-model="values.firstRowHeader" @input="reload()">{{
              $t('common.yes')
            }}</Checkbox>
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
import Papa from 'papaparse'
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
        this.error = this.$t('tableCSVImporter.limitFileSize', {
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
        this.error = this.$t('tableCSVImporter.limitError', {
          limit,
        })
        this.preview = {}
        return
      }

      Papa.parse(decodedData, {
        delimiter: this.columnSeparator === 'auto' ? '' : this.columnSeparator,
        complete: (data) => {
          if (data.data.length === 0) {
            // We need at least a single entry otherwise the user has probably chosen
            // a wrong file.
            this.values.data = ''
            this.error = this.$i18n.$t('tableCSVImporter.emptyCSV')
            this.preview = {}
          } else {
            // If parsed successfully and it is not empty then the initial data can be
            // prepared for creating the table. We store the data stringified because
            // it doesn't need to be reactive.
            const dataWithHeader = this.ensureHeaderExistsAndIsValid(
              data.data,
              this.values.firstRowHeader
            )
            this.values.data = JSON.stringify(dataWithHeader)
            this.error = ''
            this.preview = this.getPreview(dataWithHeader)
          }
        },
        error(error) {
          // Papa parse has resulted in an error which we need to display to the user.
          // All previously loaded data will be removed.
          this.values.data = ''
          this.error = error.errors[0].message
          this.preview = {}
        },
      })
    },
  },
}
</script>

<i18n>
{
  "en": {
    "tableCSVImporter": {
      "chooseFileLabel": "Choose CSV file",
      "chooseFileDescription": "You can import an existing CSV by uploading the .CSV file with tabular data. Most spreadsheet applications will allow you to export your spreadsheet as a .CSV file.",
      "chooseFile": "Choose CSV file",
      "columnSeparator": "Column separator",
      "recordSeparator": "record separator",
      "unitSeparator": "unit separator",
      "encoding": "Encoding",
      "firstRowHeader": "First row is header",
      "limitFileSize": "The maximum file size is {limit}MB.",
      "limitError": "It is not possible to import more than {limit} rows.",
      "emptyCSV": "This CSV file is empty."
    }
  },
  "fr": {
    "tableCSVImporter": {
      "chooseFileLabel": "Choisissez un fichier CSV",
      "chooseFileDescription": "Vous pouvez importer un CSV existant en envoyant un fichier .CSV avec des données tabulaires. La plupart des tableurs sont capables de réaliser un export au format CSV.",
      "chooseFile": "Choisir un fichier CSV",
      "columnSeparator": "Sép. de colonne",
      "recordSeparator": "Sép. d'enregistrement",
      "unitSeparator": "séparateur d'unité",
      "encoding": "Encodage",
      "firstRowHeader": "La première ligne est l'entête",
      "limitFileSize": "La taille maximum du fichier est de {limit}Mo.",
      "limitError": "Il n'est pas possible d'importer plus de {limit} lignes.",
      "emptyCSV": "Ce fichier CSV est vide."
    }
  }
}
</i18n>
