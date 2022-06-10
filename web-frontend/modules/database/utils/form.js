export function getPrefills(query) {
  return Object.keys(query).reduce((prefills, key) => {
    if (key.startsWith('prefill_')) {
      const keyFormatted = key
        .replace('prefill_', '') // Remove the prefix
        .replaceAll('+', ' ') // Replace + with spaces
      prefills[keyFormatted] = query[key]
    }
    return prefills
  }, Object.create(null))
}
