import { LinkElementType } from '@baserow/modules/builder/elementTypes'

describe('linkElementType', () => {
  describe('validatePathParamType', () => {
    test.each([
      [5, 'numeric', true],
      ['10', 'numeric', true],
      ['abc', 'numeric', false],
      ['hello', 'text', true],
      [123, 'text', true],
      [true, 'text', true],
      [null, 'text', true],
      ['', 'text', true],
    ])(
      'should return %p when called with value: %p and type: %p',
      (value, type, expected) => {
        const result = LinkElementType.validatePathParamType(value, type)
        expect(result).toBe(expected)
      }
    )

    test('should return false for invalid type', () => {
      const result = LinkElementType.validatePathParamType('value', 'invalid')
      expect(result).toBe(false)
    })
  })

  describe('arePathParametersInError', () => {
    test('should return false when element is not a page navigation', () => {
      const element = {
        navigation_type: 'link',
        navigate_to_page_id: 1,
      }
      const builder = {
        pages: [
          { id: 1, path_params: [] },
          { id: 2, path_params: [] },
        ],
      }

      const result = LinkElementType.arePathParametersInError(element, builder)
      expect(result).toBe(false)
    })

    test('should return false when destinationPage is not found', () => {
      const element = {
        navigation_type: 'page',
        navigate_to_page_id: 3,
      }
      const builder = {
        pages: [{ id: 1, path_params: [] }],
      }

      const result = LinkElementType.arePathParametersInError(element, builder)
      expect(result).toBe(false)
    })

    test('should return false when page parameters and destinationPage path parameters match', () => {
      const element = {
        navigation_type: 'page',
        navigate_to_page_id: 1,
        page_parameters: [
          { name: 'param1', value: '10' },
          { name: 'param2', value: 'abc' },
        ],
      }
      const builder = {
        pages: [
          {
            id: 1,
            path_params: [
              { name: 'param1', type: 'numeric' },
              { name: 'param2', type: 'text' },
            ],
          },
        ],
      }

      const result = LinkElementType.arePathParametersInError(element, builder)
      expect(result).toBe(false)
    })

    test('should return true when destinationPage path parameters length does not match page parameters length', () => {
      const element = {
        navigation_type: 'page',
        navigate_to_page_id: 1,
        page_parameters: [
          { name: 'param1', value: '10' },
          { name: 'param2', value: 'abc' },
        ],
      }
      const builder = {
        pages: [{ id: 1, path_params: [{ name: 'param1', type: 'numeric' }] }],
      }

      const result = LinkElementType.arePathParametersInError(element, builder)
      expect(result).toBe(true)
    })

    test('should return true when page parameter name or type does not match destinationPage path parameters', () => {
      const element = {
        navigation_type: 'page',
        navigate_to_page_id: 1,
        page_parameters: [
          { name: 'param1', value: '10' },
          { name: 'param3', value: 'abc' },
        ],
      }
      const builder = {
        pages: [
          {
            id: 1,
            path_params: [
              { name: 'param1', type: 'numeric' },
              { name: 'param2', type: 'text' },
            ],
          },
        ],
      }

      const result = LinkElementType.arePathParametersInError(element, builder)
      expect(result).toBe(true)
    })

    test('should return true when page parameter value fails validation for destinationPage path parameter type', () => {
      const element = {
        navigation_type: 'page',
        navigate_to_page_id: 1,
        page_parameters: [{ name: 'param1', value: 'abc' }],
      }
      const builder = {
        pages: [{ id: 1, path_params: [{ name: 'param1', type: 'numeric' }] }],
      }

      const result = LinkElementType.arePathParametersInError(element, builder)
      expect(result).toBe(true)
    })
  })
})
