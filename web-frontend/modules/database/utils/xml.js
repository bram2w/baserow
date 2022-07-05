export class XMLParser {
  constructor() {
    this.header = []
    this.errors = []
    this.xmlDoc = null
    this.xmlData = null
  }

  parse(rawXML) {
    this.xmlDoc = new window.DOMParser().parseFromString(rawXML, 'text/xml')
    const parseErrors = this.xmlDoc.getElementsByTagName('parsererror')
    if (parseErrors.length > 0) {
      Array.from(parseErrors).forEach((parseError) =>
        this.errors.push(parseError.textContent)
      )
    }
  }

  loadXML(count) {
    if (
      this.xmlDoc &&
      this.xmlDoc.documentElement &&
      this.xmlDoc.documentElement.children
    ) {
      let dataToLoad = Array.from(this.xmlDoc.documentElement.children)
      if (count) {
        dataToLoad = dataToLoad.slice(0, count)
      }
      this.xmlData = dataToLoad.map((row) => {
        const values = Array.from(row.children).map((rowChild) => {
          const rowTag = rowChild.tagName
          if (!this.header.includes(rowTag)) {
            this.header.push(rowTag)
          }
          return { tag: rowTag, value: rowChild.innerHTML }
        })
        return values
      })
    }
  }

  transform() {
    this.xmlData = this.xmlData.map((line) => {
      return this.header.map((h) => {
        const lineValue = line.filter((lv) => lv.tag === h)
        return lineValue.length > 0 ? lineValue[0].value : ''
      })
    })
    return [this.header, this.xmlData, this.errors]
  }
}

/**
 * Parses a rawXML string and extracts tabular data from it.
 */
export const parseXML = (rawXML) => {
  const parser = new XMLParser()
  parser.parse(rawXML)
  parser.loadXML()
  return parser.transform()
}
