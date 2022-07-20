import { getPrimaryOrFirstField } from '@baserow/modules/database/utils/field'

describe('test field utils', () => {
  it('should find the primary field in a list of fields', () => {
    const fields = [
      {
        name: 'id',
        type: 'integer',
        primary: true,
      },
      {
        name: 'name',
        type: 'string',
        primary: false,
      },
    ]
    const primaryField = getPrimaryOrFirstField(fields)
    expect(primaryField).toEqual(fields[0])
  })

  it('should return the first field if no primary field is found', () => {
    const fields = [
      {
        name: 'id',
        type: 'integer',
        primary: false,
      },
      {
        name: 'name',
        type: 'string',
        primary: false,
      },
    ]
    const primaryField = getPrimaryOrFirstField(fields)
    expect(primaryField).toEqual(fields[0])
  })

  it('should return undefined if no fields are provided', () => {
    const primaryField = getPrimaryOrFirstField([])
    expect(primaryField).toBeUndefined()
  })
})
