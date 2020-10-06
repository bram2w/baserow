import { firstBy } from 'thenby'

/**
 * Generates a sort function based on the provided sortings.
 */
export function getRowSortFunction($registry, sortings, fields, primary) {
  let sortFunction = firstBy()

  sortings.forEach((sort) => {
    let field = fields.find((f) => f.id === sort.field)
    if (field === undefined && primary.id === sort.field) {
      field = primary
    }

    if (field !== undefined) {
      const fieldName = `field_${field.id}`
      const fieldType = $registry.get('field', field.type)
      const fieldSortFunction = fieldType.getSort(fieldName, sort.order)
      sortFunction = sortFunction.thenBy(fieldSortFunction)
    }
  })

  sortFunction = sortFunction.thenBy((a, b) => a.id - b.id)
  return sortFunction
}
