import { isRelativeUrl } from '@baserow/modules/core/utils/url'

describe('test url utils', () => {
  describe('test isRelativeUrl', () => {
    const relativeUrls = ['/test', 'test/test', '/', '/dashboard?test=true']
    const absoluteUrls = [
      'http://example.com',
      'HTTP://EXAMPLE.COM',
      'https://www.exmaple.com',
      'ftp://example.com/file.txt',
      '//cdn.example.com/lib.js',
      'git+ssh://example.con/item',
      '////www.example.com',
      '////example.com',
      '///example.com',
    ]
    test.each(relativeUrls)('test with relative url %s', (url) => {
      expect(isRelativeUrl(url)).toBe(true)
    })
    test.each(absoluteUrls)('test with absolute url %s', (url) => {
      expect(isRelativeUrl(url)).toBe(false)
    })
  })
})
