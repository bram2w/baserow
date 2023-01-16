export const colors = [
  'light-blue',
  'light-green',
  'light-orange',
  'light-red',
  'light-gray',
  'blue',
  'green',
  'orange',
  'red',
  'gray',
  'dark-blue',
  'dark-green',
  'dark-orange',
  'dark-red',
  'dark-gray',
]

/**
 * Returns a random color from the colors array.
 * @param {Array} excludeColors - Array of colors to exclude from the random
 * selection. If undefined or equal to the colors array, no colors will be
 * excluded. Returns a random color from the colors array.
 */
export const randomColor = (excludeColors = undefined) => {
  let palette = colors
  excludeColors = excludeColors || []
  if (excludeColors.length > 0 && excludeColors.length < colors.length) {
    palette = colors.filter((color) => !excludeColors.includes(color))
  }
  return palette[Math.floor(Math.random() * palette.length)]
}
