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
        <Checkbox v-model="firstRowHeader" @input="reload()">{{
          $t('common.yes')
        }}</Checkbox>
      </div>
    </div>
    <Alert
      v-if="error !== ''"
      type="error"
      icon="exclamation"
      :title="$t('common.wrong')"
    >
      {{ error }}
    </Alert>
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

export default {
  name: 'TablePasteImporter',
  components: { TableImporterPreview },
  mixins: [form, importer],
  data() {
    return {
      content: '',
      firstRowHeader: true,
    }
  },
  validations: {
    values: {
      getData: { required },
    },
    content: { required },
  },
  methods: {
    changed(content) {
      this.$emit('changed')
      this.resetImporterState()

      this.content = content
      this.reload()
    },
    async reload() {
      if (this.content === '') {
        this.resetImporterState()
        return
      }

      const limit = this.$env.INITIAL_TABLE_DATA_LIMIT
      const count = this.content.split(/\r\n|\r|\n/).length
      if (limit !== null && count > limit) {
        this.handleImporterError(
          this.$t('tablePasteImporter.limitError', {
            limit,
          })
        )
        return
      }
      this.state = 'parsing'
      await this.$ensureRender()
      this.$papa.parse(this.content, {
        delimiter: '\t',
        complete: (parsedResult) => {
          // If parsed successfully and it is not empty then the initial data can be
          // prepared for creating the table. We store the data stringified because it
          // doesn't need to be reactive.
          let data

          if (this.firstRowHeader) {
            const [header, ...rest] = parsedResult.data
            data = rest
            this.values.header = this.prepareHeader(header, data)
          } else {
            data = parsedResult.data
            this.values.header = this.prepareHeader([], data)
          }

          this.values.getData = () => {
            return new Promise((resolve) => {
              resolve(data)
            })
          }
          this.error = ''
          this.state = null
          this.preview = this.getPreview(this.values.header, data)
        },
        error(error) {
          // Papa parse has resulted in an error which we need to display to the user.
          // All previously loaded data will be removed.
          this.handleImporterError(error.errors[0].message)
        },
      })
    },
  },
}
</script>
