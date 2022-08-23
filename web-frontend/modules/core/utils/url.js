export function isRelativeUrl(url) {
  const absoluteUrlRegExp = /^(?:[a-z+]+:)?\/\//i
  return !absoluteUrlRegExp.test(url)
}
