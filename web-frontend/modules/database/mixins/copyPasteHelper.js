/**
 * A mixin that can be used to copy and paste row values.
 */

import {
  getRichClipboard,
  setRichClipboard,
  LOCAL_STORAGE_CLIPBOARD_KEY,
} from '@baserow/modules/database/utils/clipboard'

const PAPA_CONFIG = {
  delimiter: '\t',
}

export default {
  methods: {
    prepareSelectionForCopy(fields, rows) {
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
      const text = this.$papa.unparse(textData, PAPA_CONFIG)
      try {
        localStorage.setItem(
          LOCAL_STORAGE_CLIPBOARD_KEY,
          JSON.stringify({ text, json: jsonData })
        )
        return text
      } catch (e) {
        // If the local storage is full then we just ignore it.
        // @TODO: Should we warn the user?
        return ''
      }
    },
    async copySelectionToClipboard(selectionPromise) {
      // Firefox does not have the ClipboardItem type enabled by default, so we
      // need to check if it is available. Safari instead, needs the
      // ClipboardItem type to save async data to the clipboard.
      if (typeof ClipboardItem !== 'undefined') {
        navigator.clipboard.write([
          // eslint-disable-next-line no-undef
          new ClipboardItem({
            'text/plain': selectionPromise.then(
              ([fields, rows]) =>
                new Blob([this.prepareSelectionForCopy(fields, rows)], {
                  type: 'text/plain',
                })
            ),
          }),
        ])
      } else {
        const text = await selectionPromise.then(([fields, rows]) =>
          this.prepareSelectionForCopy(fields, rows)
        )
        if (typeof navigator.clipboard?.writeText !== 'undefined') {
          navigator.clipboard.writeText(text)
        } else {
          setRichClipboard({ 'text/plain': text })
        }
      }
    },
    async extractClipboardData(event) {
      const { textRawData, jsonRawData } = await getRichClipboard(event)
      const { data: textData } = await this.$papa.parsePromise(
        textRawData,
        PAPA_CONFIG
      )

      let jsonData = null
      if (jsonRawData != null) {
        // Check if we have an array of arrays with At least one row with at least
        // one row with a value Otherwise the paste is empty
        if (
          Array.isArray(jsonRawData) &&
          jsonRawData.length === textData.length &&
          jsonRawData.every((row) => Array.isArray(row)) &&
          jsonRawData.some((row) => row.length > 0)
        ) {
          jsonData = jsonRawData
        }
      }

      return [textData, jsonData]
    },
  },
}
