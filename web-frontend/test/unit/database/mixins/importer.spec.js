/**
 * @jest-environment jsdom
 */

import importer from '@baserow/modules/database/mixins/importer'

describe('test file importer', () => {
  test('test field name id is invalid as is reserved by baserow', () => {
    expect(importer.methods.makeHeaderUniqueAndValid(['id'])).toEqual(['id 2'])
    expect(importer.methods.makeHeaderUniqueAndValid(['id', 'id 2'])).toEqual([
      'id 3',
      'id 2',
    ])
  })
  test('test field name order is invalid as is reserved by baserow', () => {
    expect(importer.methods.makeHeaderUniqueAndValid(['order'])).toEqual([
      'order 2',
    ])
    expect(
      importer.methods.makeHeaderUniqueAndValid(['order', 'order 2', 'order'])
    ).toEqual(['order 3', 'order 2', 'order 4'])
  })
  test('duplicate names are appended with numbers to make them unique', () => {
    expect(importer.methods.makeHeaderUniqueAndValid(['a', 'a', 'a'])).toEqual([
      'a',
      'a 2',
      'a 3',
    ])
    expect(
      importer.methods.makeHeaderUniqueAndValid(['a', 'a 2', 'a', 'a'])
    ).toEqual(['a', 'a 2', 'a 3', 'a 4'])
  })
  test('blank names are replaced by unique field names', () => {
    expect(importer.methods.makeHeaderUniqueAndValid(['', '', ''])).toEqual([
      'Field 1',
      'Field 2',
      'Field 3',
    ])
    expect(
      importer.methods.makeHeaderUniqueAndValid(['', 'Field 1', '', ''])
    ).toEqual(['Field 2', 'Field 1', 'Field 3', 'Field 4'])
  })
})
