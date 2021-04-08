import { uuid } from '@/modules/core/utils/string'

describe('test string utils', () => {
  test('test uuid', () => {
    const value = uuid()
    expect(typeof value).toBe('string')
  })
})
