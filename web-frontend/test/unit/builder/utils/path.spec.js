import { getPathParams } from '@baserow/modules/builder/utils/path'

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
