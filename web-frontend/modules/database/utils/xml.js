/**
 * Parses a rawXML string and extracts tabular data from it.
 */
export const parseXML = (rawXML) => {
  let xmlData = []
  const header = []
  const xmlDoc = new window.DOMParser().parseFromString(rawXML, 'text/xml')
  const parseErrors = xmlDoc.getElementsByTagName('parsererror')
  const errors = []
  if (parseErrors.length > 0) {
    Array.from(parseErrors).forEach((parseError) =>
      errors.push(parseError.textContent)
    )
  }
  if (xmlDoc && xmlDoc.documentElement && xmlDoc.documentElement.children) {
    xmlData = Array.from(xmlDoc.documentElement.children).map((row) => {
      const vals = Array.from(row.children).map((rowChild) => {
        const rowTag = rowChild.tagName
        if (!header.includes(rowTag)) {
          header.push(rowTag)
        }
        return { tag: rowTag, value: rowChild.innerHTML }
      })
      return vals
    })
  }
  xmlData = xmlData.map((line) => {
    return header.map((h) => {
      const lineValue = line.filter((lv) => lv.tag === h)
      return lineValue.length > 0 ? lineValue[0].value : ''
    })
  })
  return [header, xmlData, errors]
}
