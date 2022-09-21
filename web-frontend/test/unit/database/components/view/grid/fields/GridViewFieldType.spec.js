import { TestApp } from '@baserow/test/helpers/testApp'
import GridViewFieldType from '@baserow/modules/database/components/view/grid/GridViewFieldType'
import UpdateFieldContext from '@baserow/modules/database/components/field/UpdateFieldContext'

describe('GridViewFieldType component', () => {
  let testApp = null
  let mockServer = null

  beforeAll(() => {
    testApp = new TestApp()
    mockServer = testApp.mockServer
  })

  afterEach((done) => {
    testApp.afterEach().then(done)
  })

  const mountComponent = (props, slots = {}) => {
    return testApp.mount(GridViewFieldType, { propsData: props, slots })
  }

  const field = {
    id: 1,
    name: 'First name',
    order: 0,
    type: 'text',
    primary: false,
    text_default: '',
    _: {
      loading: false,
      type: {
        iconClass: '',
      },
    },
  }

  const populateStore = async () => {
    const table = mockServer.createTable()
    const { application } = await mockServer.createAppAndGroup(table)
    const view = mockServer.createGridView(application, table, {})
    return { table, view }
  }

  test("Field context menu isn't opened when the field name is double clicked in read only mode.", async () => {
    const { table, view } = await populateStore()

    const wrapper = await mountComponent({
      table,
      view,
      field,
      readOnly: true,
      storePrefix: 'page/',
    })

    const quickEdit = wrapper.find('.grid-view__quick-edit')
    expect(quickEdit.classes('editable')).toBe(false)
    await quickEdit.trigger('dblclick')
    await wrapper.vm.$nextTick()

    const ctx = wrapper.findComponent(UpdateFieldContext)
    expect(ctx.classes('visibility-hidden')).toBe(true)
  })

  test('Field context menu is opened when the field name is double clicked in editable mode.', async () => {
    const { table, view } = await populateStore()

    const wrapper = await mountComponent({
      table,
      view,
      field,
      readOnly: false,
      storePrefix: 'page/',
    })

    const quickEdit = wrapper.find('.grid-view__quick-edit')
    expect(quickEdit.classes('editable')).toBe(true)
    await quickEdit.trigger('dblclick')
    await wrapper.vm.$nextTick()

    const ctx = wrapper.findComponent(UpdateFieldContext)
    expect(ctx.classes('visibility-hidden')).toBe(false)
  })
})
