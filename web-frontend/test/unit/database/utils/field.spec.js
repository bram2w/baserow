import {
  getPrimaryOrFirstField,
  hasCompatibleFilterTypes,
} from '@baserow/modules/database/utils/field'
import { EqualViewFilterType } from '@baserow/modules/database/viewFilters'

describe('test field utils', () => {
  describe('getPrimaryOrFirstField', () => {
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

  describe('hasCompatibleFilterTypes', () => {
    it('should return false for a field that has no compatible type', () => {
      const field = {
        name: 'id',
        type: 'multiple_collaborators',
        primary: false,
      }
      const filterType = new EqualViewFilterType()
      expect(hasCompatibleFilterTypes(field, [filterType])).toBeFalsy()
    })

    it('should return true for a field that has a compatible type', () => {
      const field = {
        name: 'id',
        type: 'text',
        primary: false,
      }
      const filterType = new EqualViewFilterType()
      expect(hasCompatibleFilterTypes(field, [filterType])).toBeTruthy()
    })
  })
})
