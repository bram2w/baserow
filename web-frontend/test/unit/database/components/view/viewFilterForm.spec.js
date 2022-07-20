import { TestApp } from '@baserow/test/helpers/testApp'
import ViewFilterForm from '@baserow/modules/database/components/view/ViewFilterForm'

const fields = [
  {
    id: 1,
    name: 'Name',
    order: 0,
    type: 'text',
    primary: true,
    text_default: '',
    _: {
      loading: false,
    },
  },
  {
    id: 2,
    table_id: 196,
    name: 'Stars',
    order: 1,
    type: 'rating',
    primary: false,
    max_value: 5,
    color: 'dark-orange',
    style: 'star',
    _: {
      loading: false,
    },
  },
  {
    id: 3,
    table_id: 196,
    name: 'Flag',
    order: 2,
    type: 'rating',
    primary: false,
    max_value: 10,
    color: 'dark-red',
    style: 'heart',
    _: {
      loading: false,
    },
  },
]

const view = {
  id: 1,
  name: 'Grid',
  type: 'grid',
  filter_type: 'AND',
  filters: [
    {
      field: 1,
      type: 'equal',
      value: 'test',
      preload_values: {},
      _: { hover: false, loading: false },
      id: 10,
    },
    {
      field: 2,
      type: 'equal',
      value: 2,
      preload_values: {},
      _: { hover: false, loading: false },
      id: 11,
    },
  ],
  filters_disabled: false,
  _: {
    selected: true,
    loading: false,
  },
}

describe('ViewFilterForm component', () => {
  let testApp = null
  let mockServer = null

  beforeAll(() => {
    testApp = new TestApp()
    mockServer = testApp.mockServer
  })

  afterEach(() => {
    jest.useRealTimers()
    testApp.afterEach()
    mockServer.resetMockEndpoints()
  })

  const mountViewFilterForm = async (
    props = {
      fields: [],
      view: { filters: [], _: {} },
      readOnly: false,
    },
    listeners = {}
  ) => {
    const wrapper = await testApp.mount(ViewFilterForm, {
      propsData: props,
      listeners,
    })
    return wrapper
  }

  test('Default view filter component', async () => {
    const wrapper = await mountViewFilterForm()
    expect(wrapper.element).toMatchSnapshot()
  })

  test('Full view filter component', async () => {
    const wrapper = await mountViewFilterForm({
      fields,
      view,
      readOnly: false,
    })
    expect(wrapper.element).toMatchSnapshot()
  })

  test('Test rating filter', async (done) => {
    // We want to bypass some setTimeout
    jest.useFakeTimers()
    // Mock server filter update call
    mockServer.updateViewFilter(11, 5)

    // Add rating one filter
    const viewClone = JSON.parse(JSON.stringify(view))
    viewClone.filters = [
      {
        field: 2,
        type: 'equal',
        value: 2,
        preload_values: {},
        _: { hover: false, loading: false },
        id: 11,
      },
    ]

    const onChange = jest.fn(() => {
      // The test is about to finish
      expect(wrapper.emitted().changed).toBeTruthy()
      // The Five star option should be selected
      expect(wrapper.element).toMatchSnapshot()
      done()
    })

    // Mounting the component
    const wrapper = await mountViewFilterForm(
      {
        fields,
        view: viewClone,
        readOnly: false,
      },
      { changed: onChange }
    )

    // Open type dropdown
    await wrapper.find('.filters__type .dropdown__selected').trigger('click')
    expect(wrapper.element).toMatchSnapshot()

    // Select five stars
    const option = wrapper.find(
      '.filters__value  .rating > .rating__star:nth-child(5)'
    )

    await option.trigger('click')
    // Wait some timers
    await jest.runAllTimers()

    // Test finishes only when onChange callback is called
    // Wait for mockServer to respond -> see onChange callback
  })
})
