import pathToRegexp from 'path-to-regexp'

export const resolveApplicationRoute = (pages, fullPath) => {
  let found

  for (const page of pages) {
    const keys = [] // Keys are populated by the next call
    const re = pathToRegexp(page.path, keys)
    const match = re.exec(fullPath)

    if (match) {
      // The page path has matched we can stop here our search and return the result
      const [path, ...paramValues] = match
      // TODO the parameter resolution here is really simple. Should be enough for a
      // long time but we can do better here.
      const params = Object.fromEntries(
        paramValues.map((paramValue, index) => [keys[index].name, paramValue])
      )
      return [page, path, params]
    }
  }
  return found
}
