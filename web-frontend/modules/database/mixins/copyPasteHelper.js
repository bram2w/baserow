/**
 * A mixin that can be used to copy and paste row values.
 */

import { setRichClipboard } from '@baserow/modules/database/utils/clipboard'

export default {
  methods: {
    copySelectionToClipboard(fields, rows) {
      const textData = []
      const jsonData = []
      for (const row of rows) {
        const text = fields.map((field) =>
          this.$registry
            .get('field', field.type)
            .prepareValueForCopy(field, row['field_' + field.id])
        )
        const json = fields.map((field) =>
          this.$registry
            .get('field', field.type)
            .prepareRichValueForCopy(field, row['field_' + field.id])
        )
        textData.push(text)
        jsonData.push(json)
      }
      const tsv = this.$papa.unparse(textData, {
        delimiter: '\t',
      })
      const values = {
        'text/plain': tsv,
        'application/json': JSON.stringify(jsonData),
      }
      setRichClipboard(values)
    },
    async extractClipboardData(event) {
      const textRawData = event.clipboardData.getData('text/plain').trim()

      let jsonRawData
      if (event.clipboardData.types.includes('application/json')) {
        jsonRawData = event.clipboardData.getData('application/json')
      }

      const { data: textData } = await this.$papa.parsePromise(textRawData, {
        delimiter: '\t',
      })

      let jsonData = null
      if (jsonRawData) {
        try {
          const parsed = JSON.parse(jsonRawData)
          // Check if we have an array of arrays with At least one row with at least
          // one row with a value Otherwise the paste is empty
          if (
            Array.isArray(parsed) &&
            parsed.length === textData.length &&
            parsed.every((row) => Array.isArray(row)) &&
            parsed.some((row, index) => row.length > 0)
          ) {
            jsonData = JSON.parse(jsonRawData)
          }
        } catch (e) {}
      }

      return [textData, jsonData]
    },
  },
}
