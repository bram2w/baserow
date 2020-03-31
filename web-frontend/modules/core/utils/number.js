export const rounder = (digits) => {
  return parseInt('1' + Array(digits + 1).join('0'))
}

export const floor = (n, digits = 0) => {
  const r = rounder(digits)
  return Math.floor(n * r) / r
}

export const ceil = (n, digits = 0) => {
  const r = rounder(digits)
  return Math.ceil(n * r) / r
}
