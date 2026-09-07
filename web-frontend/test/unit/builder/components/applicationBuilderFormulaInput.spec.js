// `builder/enums.js` and `builder/dataProviderTypes.js` import each other, so
// the enums must be evaluated before the formula input pulls in the providers.
import { TEXT_FORMAT_TYPES } from '@baserow/modules/builder/enums'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import { splitTextMarker } from '@baserow/modules/builder/utils/markdown'
import ApplicationBuilderFormulaInput from '@baserow/modules/builder/components/ApplicationBuilderFormulaInput.vue'
import FormulaInputField from '@baserow/modules/core/components/formula/FormulaInputField.vue'

describe('ApplicationBuilderFormulaInput with the Markdown marker', () => {
  const mountInput = (value) => {
    const page = {
      id: 1,
      elements: [],
      dataSources: [],
      path_params: [{ name: 'id', type: 'text' }],
      query_params: [],
      _: { dataSourceLoading: false, dataSourceContentLoading: false },
    }
    const builder = { id: 1, theme: {}, pages: [page] }
    const mode = 'editing'

    return mountSuspended(ApplicationBuilderFormulaInput, {
      props: { modelValue: value, dataProvidersAllowed: ['page_parameter'] },
      attachTo: document.body,
      global: {
        provide: {
          workspace: {},
          builder,
          currentPage: page,
          elementPage: page,
          mode,
          applicationContext: { builder, page, mode },
        },
      },
    })
  }

  const roundTrip = async (wrapper) => {
    wrapper.findComponent(FormulaInputField).vm.emitChange()
    await wrapper.vm.$nextTick()
    return wrapper.emitted('update:modelValue').at(-1)[0]
  }

  test('shows the marker in a literal and keeps the formula through a round trip', async () => {
    const value = { formula: "'__markdown__**Terms**'", mode: 'simple' }
    const wrapper = await mountInput(value)

    expect(wrapper.find('.formula-input-field').text()).toContain(
      '__markdown__**Terms**'
    )
    expect(await roundTrip(wrapper)).toEqual(value)
    expect(splitTextMarker('__markdown__**Terms**').format).toBe(
      TEXT_FORMAT_TYPES.MARKDOWN
    )

    wrapper.unmount()
  })

  test('shows the marker before a data node and keeps the formula through a round trip', async () => {
    const value = {
      formula: "concat('__markdown__', get('page_parameter.id'))",
      mode: 'simple',
    }
    const wrapper = await mountInput(value)

    expect(wrapper.find('.formula-input-field').text()).toContain(
      '__markdown__'
    )
    expect(await roundTrip(wrapper)).toEqual(value)

    wrapper.unmount()
  })
})
