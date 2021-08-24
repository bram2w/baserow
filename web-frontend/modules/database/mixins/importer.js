/**
 * Mixin that introduces helper methods for the importer form component.
 */
import {
  RESERVED_BASEROW_FIELD_NAMES,
  MAX_FIELD_NAME_LENGTH,
} from '@baserow/modules/database/utils/constants'

export default {
  methods: {
    /**
     * Adds a header of Field 1, Field 2 etc if the first row is not already a header,
     * otherwise checks that the existing header has valid and non duplicate field
     * names. If there are invalid or duplicate field names they will be replaced with
     * valid unique field names instead.
     *
     * @param data An array starting with a header row if firstRowHeader is true,
     *    followed by rows of data.
     * @param firstRowHeader Whether or not the first row in the data array is a
     *    header row or not.
     * @return {*} An updated data object with the first row being a valid unique
     *    header row.
     */
    ensureHeaderExistsAndIsValid(data, firstRowHeader) {
      let head = data[0]
      const columns = Math.max(...data.map((entry) => entry.length))

      // If the first row is not the header, a header containing columns named
      // 'Field N' needs to be generated.
      if (!firstRowHeader) {
        head = []
        for (let i = 1; i <= columns; i++) {
          head.push(`Field ${i}`)
        }
        data.unshift(head)
      } else {
        // The header row might not be long enough to cover all columns, ensure it does
        // first.
        head = this.fill(head, columns)
        head = this.makeHeaderUniqueAndValid(head)
        data[0] = head
      }
      return data
    },
    /**
     * Fills the row with a minimum amount of empty columns.
     */
    fill(row, columns) {
      for (let i = row.length; i < columns; i++) {
        row.push('')
      }
      return row
    },
    /**
     * Generates an object that can used to render a quick preview of the provided
     * data. Can be used in combination with the TableImporterPreview component.
     */
    getPreview(data) {
      const head = data[0]
      const rows = data.slice(1, 4)
      const remaining = data.length - rows.length - 1
      const columns = Math.max(...data.map((entry) => entry.length))

      rows.map((row) => this.fill(row, columns))

      return { columns, head, rows, remaining }
    },
    /**
     * Find the next un-unused column not present or used yet in the nextFreeIndexMap.
     * Will append a number to the returned columnName if it is taken, where that
     * number ensures the returned name is unique. Will respect the maximum allowed
     * field name length. Finally this function will update
     * the nextFreeIndexMap so future calls will not use any columns returned by
     * this function.
     * @param originalColumnName The column name to find the next free unique value for.
     * @param nextFreeIndexMap A map of column name to next free starting index.
     * @param startingIndex The starting index to start from if no index is found in
     *    the map.
     * @return {string} A column name possibly postfixed with a number to ensure it
     *    is unique.
     */
    findNextFreeName(originalColumnName, nextFreeIndexMap, startingIndex) {
      let i = nextFreeIndexMap.get(originalColumnName) || startingIndex
      while (true) {
        const suffixToAppend = ` ${i}`
        let nextColumnNameToCheck

        // If appending a number to the columnName in order to make it
        // unique will return a string that is longer than the maximum
        // allowed field name length, we need to further slice the
        // columnName as to not go above the maximum allowed length.
        if (
          originalColumnName.length + suffixToAppend.length >
          MAX_FIELD_NAME_LENGTH
        ) {
          nextColumnNameToCheck = `${originalColumnName.slice(
            0,
            -suffixToAppend.length
          )}${suffixToAppend}`
        } else {
          nextColumnNameToCheck = `${originalColumnName}${suffixToAppend}`
        }
        if (!nextFreeIndexMap.has(nextColumnNameToCheck)) {
          nextFreeIndexMap.set(originalColumnName, i + 1)
          return nextColumnNameToCheck
        }
        i++
      }
    },
    /**
     * Given a column name this function will return a new name which is guarrenteed
     * to be unique and valid. If the originally provided name is unique and valid
     * then it will be returned untouched.
     *
     * @param column The column name to check.
     * @param nextFreeIndexMap A map of column names to an index number. A value of 0
     *    indicates that the key is a column name which exists in the table but has not
     *    yet been returned yet. A number higher than 0 indicates that the column has
     *    already occurred and the index needs to be appended to the name to generate a
     *    new unique column name.
     * @return {string|*} A valid unique column name.
     */
    makeColumnNameUniqueAndValidIfNotAlready(column, nextFreeIndexMap) {
      if (column === '') {
        return this.findNextFreeName('Field', nextFreeIndexMap, 1)
      } else if (RESERVED_BASEROW_FIELD_NAMES.includes(column)) {
        return this.findNextFreeName(column, nextFreeIndexMap, 2)
      } else if (nextFreeIndexMap.get(column) > 0) {
        return this.findNextFreeName(column, nextFreeIndexMap, 2)
      } else {
        nextFreeIndexMap.set(column, 2)
        return column
      }
    },
    /**
     * Ensures that the uploaded field names are unique, non blank, don't exceed
     * the maximum field name length and don't use any reserved Baserow field names.
     * @param {*[]} head An array of field names to be checked.
     * @return A new array of field names which are guaranteed to be unique and valid.
     */
    makeHeaderUniqueAndValid(head) {
      const nextFreeIndexMap = new Map()
      for (let i = 0; i < head.length; i++) {
        const truncatedColumn = head[i].trim().slice(0, MAX_FIELD_NAME_LENGTH)
        nextFreeIndexMap.set(truncatedColumn, 0)
      }
      const uniqueAndValidHeader = []
      for (let i = 0; i < head.length; i++) {
        const column = head[i]
        const trimmedColumn = column.trim()
        const truncatedColumn = trimmedColumn.slice(0, MAX_FIELD_NAME_LENGTH)
        const uniqueValidName = this.makeColumnNameUniqueAndValidIfNotAlready(
          truncatedColumn,
          nextFreeIndexMap
        )
        uniqueAndValidHeader.push(uniqueValidName)
      }
      return uniqueAndValidHeader
    },
  },
}
