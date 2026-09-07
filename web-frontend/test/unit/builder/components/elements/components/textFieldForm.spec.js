import { MARKDOWN_PREFIX } from '@baserow/modules/core/formula/textFormat'
import TextFieldForm from '@baserow/modules/builder/components/elements/components/collectionField/form/TextFieldForm'

import { mountSuspended } from '@nuxt/test-utils/runtime'
import { h } from 'vue'

describe('TextFieldForm', () => {
  let wrapper

  const defaultProps = {
    element: { id: 1, type: 'table', fields: [] },
    baseTheme: {},
    defaultValues: {
      value: { formula: 'test text' },
      styles: {},
      // Add some non-allowed properties
      someOtherProp: 'should not be included',
      anotherProp: 123,
    },
  }

  const mountComponent = (props = {}) => {
    return mountSuspended(TextFieldForm, {
      props: {
        ...defaultProps,
        ...props,
      },
      mocks: {
        $t: (key) => key,
        $registry: {
          getOrderedList: () => [],
        },
      },
      global: {
        provide: {
          workspace: {},
          builder: {
            theme: {},
          },
          currentPage: {},
          elementPage: {},
          mode: 'edit',
          formulaComponent: () => h('div', `fake formula component`),
          dataProvidersAllowed: [],
          openCustomStyleForm: vi.fn(),
        },
      },
      stubs: {
        FormGroup: true,
        RadioGroup: true,
        InjectedFormulaInput: true,
        CustomStyle: true,
      },
    })
  }

  beforeEach(async () => {
    wrapper = await mountComponent()
  })

  afterEach(() => {
    wrapper.unmount()
  })

  test('writes the format into the value formula', async () => {
    // Verify initial state
    expect(wrapper.vm.allowedValues).toEqual(['value', 'styles'])
    const formatSelector = wrapper.findComponent({ name: 'TextFormatSelector' })
    expect(formatSelector.props('modelValue')).toBe('plain')

    // Simulate a format change
    await formatSelector.vm.$emit('update:modelValue', 'markdown')

    // Get the last emitted values-changed event
    const emittedValues = wrapper.emitted('values-changed')
    expect(emittedValues).toBeTruthy()
    const lastEmittedValues = emittedValues[emittedValues.length - 1][0]

    // Verify only allowed values are present
    expect(Object.keys(lastEmittedValues)).toEqual(['value', 'styles'])
    expect(lastEmittedValues).toEqual({
      value: { formula: `${MARKDOWN_PREFIX}test text` },
      styles: {},
    })
    expect(formatSelector.props('modelValue')).toBe('markdown')

    // Verify non-allowed values are not present
    expect(lastEmittedValues.someOtherProp).toBeUndefined()
    expect(lastEmittedValues.anotherProp).toBeUndefined()
  })
})
