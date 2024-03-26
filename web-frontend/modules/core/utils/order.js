/**
 * This function lets you create a new order for an object that is between 2 other
 * objects. It won't match exactly what the backend will calculate but it approximates
 * it.
 *
 * @param beforeOrder
 * @param afterOrder
 * @returns {string|*}
 */
import BigNumber from 'bignumber.js'

export function calculateTempOrder(beforeOrder, afterOrder) {
  if (beforeOrder === null && afterOrder === null) {
    return '1'
  }

  if (afterOrder === null) {
    const beforeOrderCasted = new BigNumber(beforeOrder)
    return beforeOrderCasted.plus(1).toString()
  }

  if (beforeOrder === null) {
    const afterOrderCasted = new BigNumber(afterOrder)
    return afterOrderCasted.dividedBy(2).toString()
  }

  const beforeOrderCasted = new BigNumber(beforeOrder)
  const afterOrderCasted = new BigNumber(afterOrder)
  return beforeOrderCasted.plus(afterOrderCasted).dividedBy(2).toString()
}
