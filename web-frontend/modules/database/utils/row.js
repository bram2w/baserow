/**
 * Serializes a row to make sure that the values are according to what the API expects.
 *
 * If a field doesn't have a value it will be assigned the empty value of the field
 * type.
 */
export function prepareRowForRequest(row, fields, registry) {
  return fields.reduce((preparedRow, field) => {
    const name = `field_${field.id}`
    const fieldType = registry.get('field', field._.type.type)

    if (fieldType.isReadOnly) {
      return preparedRow
    }

    preparedRow[name] = Object.prototype.hasOwnProperty.call(row, name)
      ? (preparedRow[name] = fieldType.prepareValueForUpdate(field, row[name]))
      : fieldType.getEmptyValue(field)

    return preparedRow
  }, {})
}
