// `builder/enums` and `builder/dataProviderTypes` import each other. Entering
// the cycle through the component would evaluate the enums first with the data
// provider types still undefined, so the enums are loaded up front, like the
// builder plugin does in the app.
import '@baserow/modules/builder/enums'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import { defineComponent, h } from 'vue'
import ApplicationBuilderFormulaInput from '@baserow/modules/builder/components/ApplicationBuilderFormulaInput.vue'
import { MARKDOWN_PREFIX } from '@baserow/modules/core/formula/textFormat'

/**
 * The formula editor is replaced by a stub that renders the formula it is
 * given and emits whatever the test types.
 */
const FormulaInputFieldStub = defineComponent({
  name: 'FormulaInputField',
  props: { value: { type: String, default: '' }, mode: { type: String } },
  emits: ['input'],
  render() {
    return h('div', { class: 'formula-input-field-stub' }, this.value)
  },
})

describe('ApplicationBuilderFormulaInput', () => {
  const page = { id: 1, elements: [], _: { dataSourceLoading: false } }

  const mountComponent = (value) =>
    mountSuspended(ApplicationBuilderFormulaInput, {
      props: { value, dataProvidersAllowed: [] },
      global: {
        provide: {
          elementPage: page,
          applicationContext: { page, builder: { id: 1 }, mode: 'editing' },
        },
        stubs: { FormulaInputField: FormulaInputFieldStub },
      },
    })

  test('never shows the text format marker in the editor', async () => {
    const wrapper = await mountComponent({
      formula: `${MARKDOWN_PREFIX}get('page_parameter.id')`,
      mode: 'simple',
      version: '0.1',
    })

    const editor = wrapper.findComponent({ name: 'FormulaInputField' })
    expect(editor.props('value')).toBe("get('page_parameter.id')")
    expect(wrapper.text()).not.toContain(MARKDOWN_PREFIX)
  })

  test('adds the marker back to what the editor emits', async () => {
    const wrapper = await mountComponent({
      formula: `${MARKDOWN_PREFIX}get('page_parameter.id')`,
      mode: 'simple',
      version: '0.1',
    })

    const editor = wrapper.findComponent({ name: 'FormulaInputField' })
    await editor.vm.$emit('input', "concat('a', get('page_parameter.id'))")

    const expected = {
      formula: `${MARKDOWN_PREFIX}concat('a', get('page_parameter.id'))`,
      mode: 'simple',
      version: '0.1',
    }
    expect(wrapper.emitted('input')).toEqual([[expected]])
    expect(wrapper.emitted('update:modelValue')).toEqual([[expected]])
  })

  test('keeps the marker when the editor is emptied', async () => {
    const wrapper = await mountComponent({
      formula: `${MARKDOWN_PREFIX}'a'`,
      mode: 'simple',
    })

    const editor = wrapper.findComponent({ name: 'FormulaInputField' })
    await editor.vm.$emit('input', '')

    expect(wrapper.emitted('input')[0][0].formula).toBe(MARKDOWN_PREFIX)
  })

  test('leaves plain formulas alone', async () => {
    const wrapper = await mountComponent({ formula: "'a'", mode: 'simple' })

    const editor = wrapper.findComponent({ name: 'FormulaInputField' })
    expect(editor.props('value')).toBe("'a'")
    await editor.vm.$emit('input', "'b'")

    expect(wrapper.emitted('input')[0][0].formula).toBe("'b'")
  })
})
