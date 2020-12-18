import { firstBy } from 'thenby'
import BigNumber from 'bignumber.js'

/**
 * Generates a sort function based on the provided sortings.
 */
export function getRowSortFunction(
  $registry,
  sortings,
  fields,
  primary = null
) {
  let sortFunction = firstBy()

  sortings.forEach((sort) => {
    // Find the field that is related to the sort.
    let field = fields.find((f) => f.id === sort.field)
    if (field === undefined && primary !== null && primary.id === sort.field) {
      field = primary
    }

    if (field !== undefined) {
      const fieldName = `field_${field.id}`
      const fieldType = $registry.get('field', field.type)
      const fieldSortFunction = fieldType.getSort(fieldName, sort.order)
      sortFunction = sortFunction.thenBy(fieldSortFunction)
    }
  })

  sortFunction = sortFunction.thenBy((a, b) =>
    new BigNumber(a.order).minus(new BigNumber(b.order))
  )
  sortFunction = sortFunction.thenBy((a, b) => a.id - b.id)
  return sortFunction
}
