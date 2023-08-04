import {
  ensureInteger,
  ensureString,
} from '@baserow/modules/core/utils/validator'

describe('ensureInteger', () => {
  it('should return the value as an integer if it is already an integer', () => {
    expect(ensureInteger(5)).toBe(5)
    expect(ensureInteger(-10)).toBe(-10)
  })

  it('should convert a string representation of an integer to an integer', () => {
    expect(ensureInteger('15')).toBe(15)
    expect(ensureInteger('-20')).toBe(-20)
  })

  it('should throw an error if the value is not a valid integer', () => {
    expect(() => ensureInteger('abc')).toThrow(Error)
    expect(() => ensureInteger('12.34')).toThrow(Error)
    expect(() => ensureInteger(true)).toThrow(Error)
    expect(() => ensureInteger(null)).toThrow(Error)
  })
})

describe('ensureString', () => {
  it('should return an empty string if the value is falsy', () => {
    expect(ensureString(null)).toBe('')
    expect(ensureString(undefined)).toBe('')
    expect(ensureString('')).toBe('')
  })

  it('should convert the value to a string if it is truthy', () => {
    expect(ensureString(5)).toBe('5')
    expect(ensureString(true)).toBe('true')
    expect(ensureString(0)).toBe('0')
    expect(ensureString(false)).toBe('false')
    expect(ensureString([1, 2, 3])).toBe('1,2,3')
    expect(ensureString({ key: 'value' })).toBe('[object Object]')
  })
})
