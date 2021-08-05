import {
  uuid,
  upperCaseFirst,
  slugify,
  isValidURL,
  isValidEmail,
  isSecureURL,
} from '@/modules/core/utils/string'
import { isNumeric } from '@baserow/modules/core/utils/string'

describe('test string utils', () => {
  test('test uuid', () => {
    const value = uuid()
    expect(typeof value).toBe('string')
  })

  test('test upperCaseFirst', () => {
    expect(upperCaseFirst('test string')).toBe('Test string')
    expect(upperCaseFirst('Test string')).toBe('Test string')
    expect(upperCaseFirst('TEST string')).toBe('TEST string')
    expect(upperCaseFirst('tEST String')).toBe('TEST String')
    expect(upperCaseFirst('test')).toBe('Test')
    expect(upperCaseFirst('a')).toBe('A')
    expect(upperCaseFirst('A')).toBe('A')
    expect(upperCaseFirst('')).toBe('')
  })

  test('test slugify', () => {
    expect(slugify('')).toBe('')
    expect(slugify('test')).toBe('test')
    expect(slugify('This is A test')).toBe('this-is-a-test')
    expect(slugify('/ā/t+?,.;!@')).toBe('a-t')
    expect(slugify('/a&--b/')).toBe('a-and-b')
  })

  test('test isValidURL', () => {
    expect(isValidURL('not-a-url')).toBe(false)
    expect(isValidURL('')).toBe(false)
    expect(isValidURL('htt://test.nl')).toBe(false)
    expect(isValidURL('http:/test.nl')).toBe(false)
    expect(isValidURL('http://test.nl')).toBe(true)
    expect(isValidURL('https://test.nl')).toBe(true)
    expect(isValidURL('ftp://test.nl')).toBe(true)
    expect(isValidURL('random://test.nl')).toBe(false)
    expect(isValidURL('https://test.nl?url=test')).toBe(true)
    expect(isValidURL('http://test.nl:8000/test')).toBe(true)
    expect(isValidURL('ftp://127.0.0.1')).toBe(true)
    expect(isValidURL('ftp://sub.domain.nl')).toBe(true)
    expect(isValidURL('https://sub.sub.domain.nl')).toBe(true)
    expect(isValidURL('HTTPS://sub.SUB.domain.NL')).toBe(true)
  })

  test('test isValidEmail', () => {
    const invalidEmails = [
      'test@' + 'a'.repeat(246) + '.com',
      '@a',
      'a@',
      'not-an-email',
      'bram.test.nl',
      'invalid_email',
      'invalid@invalid@com',
      '\nhello@gmail.com',
      'asdds asdd@gmail.com',
    ]

    const validEmails = [
      'test@' + 'a'.repeat(245) + '.com',
      'a@a',
      '用户@例子.广告',
      'अजय@डाटा.भारत',
      'квіточка@пошта.укр',
      'χρήστης@παράδειγμα.ελ',
      'Dörte@Sörensen.example.com',
      'коля@пример.рф',
      'bram@localhost',
      'bram@localhost.nl',
      'first_part_underscores_ok@hyphens-ok.com',
      'wierd@[1.1.1.1]',
      'bram.test.test@sub.domain.nl',
      'BRAM.test.test@sub.DOMAIN.nl',
    ]

    for (const invalidEmail of invalidEmails) {
      expect(isValidEmail(invalidEmail)).toBe(false)
    }
    for (const validEmail of validEmails) {
      expect(isValidEmail(validEmail)).toBe(true)
    }
  })

  test('test isSecureURL', () => {
    expect(isSecureURL('test')).toBe(false)
    expect(isSecureURL('http://test.nl')).toBe(false)
    expect(isSecureURL('https://test.nl')).toBe(true)
    expect(isSecureURL('HTTPS://test.nl')).toBe(true)
    expect(isSecureURL('https://test.domain.nl?test=test')).toBe(true)
  })

  test('test isNumeric', () => {
    expect(isNumeric('a')).toBe(false)
    expect(isNumeric('1.2')).toBe(false)
    expect(isNumeric('')).toBe(false)
    expect(isNumeric('null')).toBe(false)
    expect(isNumeric('12px')).toBe(false)
    expect(isNumeric('1')).toBe(true)
    expect(isNumeric('9999')).toBe(true)
    expect(isNumeric('-100')).toBe(true)
  })
})
