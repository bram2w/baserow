export function getPrefills(query) {
  return Object.keys(query).reduce((prefills, key) => {
    if (key.startsWith('prefill_')) {
      const keyFormatted = key
        .replace('prefill_', '') // Remove the prefix
        .replaceAll('+', ' ') // Replace + with spaces
      let valueChosen = query[key]
      if (Array.isArray(query[key])) {
        valueChosen = valueChosen[valueChosen.length - 1]
      }
      prefills[keyFormatted] = valueChosen
    }
    return prefills
  }, Object.create(null))
}

export function getHiddenFieldNames(query) {
  return Object.keys(query)
    .filter((key) => {
      return key.startsWith('hide_')
    })
    .map((key) => {
      return key.replace('hide_', '').replaceAll('+', ' ')
    })
}
