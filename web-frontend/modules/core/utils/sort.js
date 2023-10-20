/**
 * Sorts an array of numbers and uuid_v1 ascending, putting numbers before
 * uuid_v1.
 * @param {*} a: a number or a uuid v1
 * @param {*} b: a number or a uuid v1
 * @returns -1 if a < b, 0 if a == b, 1 if a > b
 */
export const sortNumbersAndUuid1Asc = (a, b) => {
  const isANumber = Number.isInteger(a.id)
  const isBNumber = Number.isInteger(b.id)

  if (isANumber && isBNumber) {
    return a.id - b.id
  }

  if (isANumber && !isBNumber) {
    return -1
  }

  if (!isANumber && isBNumber) {
    return 1
  }

  if (!isANumber && !isBNumber) {
    return a.id.localeCompare(b.id)
  }
}
