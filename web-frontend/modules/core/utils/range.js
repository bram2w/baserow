/**
 * Calculates the difference between two ranges.
 *
 * @param {Array} range1 - The first range, represented as an array [start1, end1].
 * @param {Array} range2 - The second range, represented as an array [start2, end2].
 * @returns {Array|null} - Returns an array [lowerBound, upperBound] representing the difference between the two ranges.
 *                         Returns null if the second range is entirely within the first range.
 */
export function rangeDiff(range1, range2) {
  const [start1, end1] = range1
  const [start2, end2] = range2

  // Check if the second range is included in the first one
  if (start1 <= start2 && end1 >= end2) {
    return null
  }

  const lowerBound = Math.max(end1, start2)
  const upperBound = Math.max(end1, end2)

  return [lowerBound, upperBound]
}
