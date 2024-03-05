import { ElementType } from '@baserow/modules/builder/elementTypes'
import { TestApp } from '@baserow/test/helpers/testApp'

describe('elementTypes tests', () => {
  const testApp = new TestApp()

  const contextBlankParam = { page: { parameters: { id: '' } } }

  describe('elementType getDisplayName permutation tests', () => {
    test('ElementType returns the name by default', () => {
      const elementType = new ElementType()
      expect(elementType.getDisplayName({}, {})).toBe(null)
    })
    test('ColumnElementType returns the name by default', () => {
      const elementType = testApp.getRegistry().get('element', 'column')
      expect(elementType.getDisplayName({}, {})).toBe('elementType.column')
    })
    test('InputTextElementType label and default_value variations', () => {
      const elementType = testApp.getRegistry().get('element', 'input_text')
      expect(elementType.getDisplayName({ label: "'First name'" }, {})).toBe(
        'First name'
      )
      expect(
        elementType.getDisplayName(
          { default_value: "'Enter a first name'" },
          {}
        )
      ).toBe('Enter a first name')
      expect(
        elementType.getDisplayName(
          { placeholder: "'Choose a first name...'" },
          {}
        )
      ).toBe('Choose a first name...')
      // If a formula resolves to a blank string, fallback to the name.
      expect(
        elementType.getDisplayName(
          { label: "get('page_parameter.id')" },
          contextBlankParam
        )
      ).toBe(elementType.name)
      expect(elementType.getDisplayName({}, {})).toBe(elementType.name)
    })
    test('DropdownElementType label, default_value & placeholder variations', () => {
      const elementType = testApp.getRegistry().get('element', 'dropdown')
      expect(elementType.getDisplayName({ label: "'Animals'" }, {})).toBe(
        'Animals'
      )
      expect(elementType.getDisplayName({ default_value: "'Horse'" }, {})).toBe(
        'Horse'
      )
      expect(
        elementType.getDisplayName({ default_value: "'Choose an animal'" }, {})
      ).toBe('Choose an animal')
      // If a formula resolves to a blank string, fallback to the name.
      expect(
        elementType.getDisplayName(
          { label: "get('page_parameter.id')" },
          contextBlankParam
        )
      ).toBe(elementType.name)
      expect(elementType.getDisplayName({}, {})).toBe(elementType.name)
    })
    test('CheckboxElementType with and without a label to use', () => {
      const elementType = testApp.getRegistry().get('element', 'checkbox')
      expect(elementType.getDisplayName({ label: "'Active'" }, {})).toBe(
        'Active'
      )
      // If a formula resolves to a blank string, fallback to the name.
      expect(
        elementType.getDisplayName(
          { label: "get('page_parameter.id')" },
          contextBlankParam
        )
      ).toBe(elementType.name)
      expect(elementType.getDisplayName({}, {})).toBe(elementType.name)
    })
    test('HeadingElementType with and without a value to use', () => {
      const elementType = testApp.getRegistry().get('element', 'heading')
      expect(elementType.getDisplayName({ value: "'A heading'" }, {})).toBe(
        'A heading'
      )
      // If a formula resolves to a blank string, fallback to the name.
      expect(
        elementType.getDisplayName(
          { value: "get('page_parameter.id')" },
          contextBlankParam
        )
      ).toBe(elementType.name)
      expect(elementType.getDisplayName({}, {})).toBe(elementType.name)
    })
    test('TextElementType with and without a value to use', () => {
      const elementType = testApp.getRegistry().get('element', 'text')
      expect(elementType.getDisplayName({ value: "'Some text'" }, {})).toBe(
        'Some text'
      )
      // If a formula resolves to a blank string, fallback to the name.
      expect(
        elementType.getDisplayName(
          { value: "get('page_parameter.id')" },
          contextBlankParam
        )
      ).toBe(elementType.name)
      expect(elementType.getDisplayName({}, {})).toBe(elementType.name)
    })
    test('LinkElementType page and custom URL variations', () => {
      const elementType = testApp.getRegistry().get('element', 'link')
      const applicationContext = {
        builder: {
          pages: [{ id: 1, name: 'Contact Us' }],
        },
      }
      expect(
        elementType.getDisplayName(
          {
            navigate_to_page_id: 1,
            navigation_type: 'page',
          },
          applicationContext
        )
      ).toBe('elementType.link -> Contact Us')

      // If we were not able to find the page, we fall back to trying for a value.
      expect(
        elementType.getDisplayName(
          {
            value: "'Click me'",
            navigate_to_page_id: 2,
            navigation_type: 'page',
          },
          applicationContext
        )
      ).toBe('Click me')

      // If we were not able to find the page, and there's no value, we fall back to the name.
      expect(
        elementType.getDisplayName(
          {
            navigate_to_page_id: 2,
            navigation_type: 'page',
          },
          applicationContext
        )
      ).toBe(elementType.name)

      expect(
        elementType.getDisplayName(
          {
            navigation_type: 'custom',
            navigate_to_url: "'https://baserow.io'",
            value: "'Link name'",
          },
          applicationContext
        )
      ).toBe('Link name -> https://baserow.io')
    })
    test('ImageElementType with and without alt text to use', () => {
      const elementType = testApp.getRegistry().get('element', 'image')
      expect(
        elementType.getDisplayName({ alt_text: "'Baserow logo'" }, {})
      ).toBe('Baserow logo')
      // If a formula resolves to a blank string, fallback to the name.
      expect(
        elementType.getDisplayName(
          { alt_text: "get('page_parameter.id')" },
          contextBlankParam
        )
      ).toBe(elementType.name)
      expect(elementType.getDisplayName({}, {})).toBe(elementType.name)
    })
    test('ButtonElementType with and without value to use', () => {
      const elementType = testApp.getRegistry().get('element', 'button')
      expect(elementType.getDisplayName({ value: "'Click me'" }, {})).toBe(
        'Click me'
      )
      // If a formula resolves to a blank string, fallback to the name.
      expect(
        elementType.getDisplayName(
          { value: "get('page_parameter.id')" },
          contextBlankParam
        )
      ).toBe(elementType.name)
      expect(elementType.getDisplayName({}, {})).toBe(elementType.name)
    })
    test('TableElementType with and without data_source_id to use', () => {
      const elementType = testApp.getRegistry().get('element', 'table')
      const page = {
        id: 1,
        name: 'Contact Us',
        dataSources: [
          { id: 1, type: 'local_baserow_list_rows', name: 'Customers' },
        ],
      }
      const applicationContext = {
        page,
        builder: { pages: [page] },
      }
      expect(
        elementType.getDisplayName({ data_source_id: 1 }, applicationContext)
      ).toBe('elementType.table - Customers')

      // In the event we don't find the data source.
      expect(
        elementType.getDisplayName({ data_source_id: 2 }, applicationContext)
      ).toBe(elementType.name)

      expect(elementType.getDisplayName({}, applicationContext)).toBe(
        elementType.name
      )
    })
    test('FormContainerElementType returns the name by default', () => {
      const elementType = testApp.getRegistry().get('element', 'form_container')
      expect(elementType.getDisplayName({}, {})).toBe(elementType.name)
    })
    test('IFrameElementType with and without a url to use', () => {
      const elementType = testApp.getRegistry().get('element', 'iframe')
      expect(
        elementType.getDisplayName(
          { url: "'https://www.youtube.com/watch?v=dQw4w9WgXcQ'" },
          {}
        )
      ).toBe('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
      expect(elementType.getDisplayName({}, {})).toBe(elementType.name)
    })
  })
})
