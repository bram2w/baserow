<template>
  <div>
    <div class="control">
      <label class="control__label">{{
        $t('tablePasteImporter.pasteLabel')
      }}</label>
      <div class="control__description">
        {{ $t('tablePasteImporter.pasteDescription') }}
      </div>
      <div class="control__elements">
        <textarea
          type="text"
          class="input input--large textarea--modal"
          @input="changed($event.target.value)"
        ></textarea>
        <div v-if="$v.content.$error" class="error">
          {{ $t('error.fieldRequired') }}
        </div>
      </div>
    </div>
    <div class="control">
      <label class="control__label">{{
        $t('tablePasteImporter.firstRowHeader')
      }}</label>
      <div class="control__elements">
        <Checkbox v-model="values.firstRowHeader" @input="reload()">{{
          $t('common.yes')
        }}</Checkbox>
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
      v-if="error === '' && content !== '' && Object.keys(preview).length !== 0"
      :preview="preview"
    ></TableImporterPreview>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import importer from '@baserow/modules/database/mixins/importer'
import TableImporterPreview from '@baserow/modules/database/components/table/TableImporterPreview'
import Papa from 'papaparse'

export default {
  name: 'TablePasteImporter',
  components: { TableImporterPreview },
  mixins: [form, importer],
  data() {
    return {
      values: {
        data: '',
        firstRowHeader: true,
      },
      content: '',
      error: '',
      preview: {},
    }
  },
  validations: {
    values: {
      data: { required },
    },
    content: { required },
  },
  methods: {
    changed(content) {
      this.content = content
      this.reload()
    },
    reload() {
      if (this.content === '') {
        this.values.data = ''
        this.error = ''
        this.preview = {}
        this.$emit('input', this.value)
        return
      }

      const limit = this.$env.INITIAL_TABLE_DATA_LIMIT || 1
      const count = this.content.split(/\r\n|\r|\n/).length
      if (limit !== null && count > limit) {
        this.values.data = ''
        this.error = this.$t('tablePasteImporter.limitError', {
          limit,
        })
        this.preview = {}
        this.$emit('input', this.value)
        return
      }

      Papa.parse(this.content, {
        delimiter: '\t',
        complete: (data) => {
          // If parsed successfully and it is not empty then the initial data can be
          // prepared for creating the table. We store the data stringified because it
          // doesn't need to be reactive.
          const dataWithHeader = this.ensureHeaderExistsAndIsValid(
            data.data,
            this.values.firstRowHeader
          )
          this.values.data = JSON.stringify(dataWithHeader)
          this.error = ''
          this.preview = this.getPreview(dataWithHeader)
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

<i18n>
{
  "en": {
    "tablePasteImporter": {
      "pasteLabel": "Paste the table data",
      "pasteDescription": "You can copy the cells from a spreadsheet and paste them below.",
      "firstRowHeader": "First row is header",
      "limitError": "It is not possible to import more than {limit} rows."
    }
  },
  "fr": {
    "tablePasteImporter": {
      "pasteLabel": "Collez les données tabulaires",
      "pasteDescription": "Vous pouvez copier les lignes provenant d'un tableur et les coller ci-dessous.",
      "firstRowHeader": "La première ligne est l'entête",
      "limitError": "Il n'est pas possible d'importer plus de {limit} lignes."
    }
  }
}
</i18n>
