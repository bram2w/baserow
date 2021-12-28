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

export const randomColor = () => {
  return colors[Math.floor(Math.random() * colors.length)]
}
