export const colors = [
  'light-blue',
  'light-green',
  'light-cyan',
  'light-yellow',
  'light-orange',
  'light-red',
  'light-brown',
  'light-purple',
  'light-pink',
  'light-gray',
  'blue',
  'green',
  'cyan',
  'yellow',
  'orange',
  'red',
  'brown',
  'purple',
  'pink',
  'gray',
  'dark-blue',
  'dark-green',
  'dark-cyan',
  'dark-yellow',
  'dark-orange',
  'dark-red',
  'dark-brown',
  'dark-purple',
  'dark-pink',
  'dark-gray',
  'darker-blue',
  'darker-green',
  'darker-cyan',
  'darker-yellow',
  'darker-orange',
  'darker-red',
  'darker-brown',
  'darker-purple',
  'darker-pink',
  'darker-gray',
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
