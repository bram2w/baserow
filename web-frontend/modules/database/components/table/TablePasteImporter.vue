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
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import importer from '@baserow/modules/database/mixins/importer'

export default {
  name: 'TablePasteImporter',
  mixins: [form, importer],
  data() {
    return {
      content: '',
      firstRowHeader: true,
    }
  },
  validations: {
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
          let header

          if (this.firstRowHeader) {
            const [rawHeader, ...rest] = parsedResult.data
            data = rest
            header = this.prepareHeader(rawHeader, data)
          } else {
            data = parsedResult.data
            header = this.prepareHeader([], data)
          }

          const getData = () => {
            return new Promise((resolve) => {
              resolve(data)
            })
          }
          this.error = ''
          this.state = null
          const previewData = this.getPreview(header, data)
          this.$emit('getData', getData)
          this.$emit('data', { header, previewData })
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
