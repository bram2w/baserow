import { getPathParams, splitPath } from '@baserow/modules/builder/utils/path'

describe('getPathParams', () => {
  test('that it can find no params', () => {
    expect(getPathParams('/test')).toEqual([])
  })
  test('that it can find one param', () => {
    expect(getPathParams('/test/:id')).toEqual(['id'])
  })
  test('that it can find multiple params', () => {
    expect(getPathParams('/test/:id/:test')).toEqual(['id', 'test'])
  })
  test('that it can find multiple params without slashes', () => {
    expect(getPathParams('/test/:id-:test')).toEqual(['id', 'test'])
  })
  test('that it can find multiple params with double colons', () => {
    expect(getPathParams('/test/::test')).toEqual(['test'])
  })
})

describe('splitPath', () => {
  test('should split path with variables correctly', () => {
    const path = '/users/:id/profile'
    const expectedParts = [
      { value: '/users/', type: 'path' },
      { value: 'id', type: 'variable' },
      { value: '/profile', type: 'path' },
    ]

    const result = splitPath(path)
    expect(result).toEqual(expectedParts)
  })

  test('should split path with multiple variables correctly', () => {
    const path = '/articles/:slug/comments/:id'
    const expectedParts = [
      { value: '/articles/', type: 'path' },
      { value: 'slug', type: 'variable' },
      { value: '/comments/', type: 'path' },
      { value: 'id', type: 'variable' },
    ]

    const result = splitPath(path)
    expect(result).toEqual(expectedParts)
  })

  test('should split path with only fixed parts correctly', () => {
    const path = '/about/contact'
    const expectedParts = [{ value: '/about/contact', type: 'path' }]

    const result = splitPath(path)
    expect(result).toEqual(expectedParts)
  })
})
