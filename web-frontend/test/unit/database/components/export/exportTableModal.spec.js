import { TestApp } from '@baserow/test/helpers/testApp'
import ExportTableModal from '@baserow/modules/database/components/export/ExportTableModal'

describe('Preview exportTableModal', () => {
  let testApp = null
  let mockServer = null

  beforeAll(() => {
    testApp = new TestApp()
    mockServer = testApp.mockServer
  })

  afterEach(() => {
    testApp.afterEach()
  })

  async function givenThereIsATableWithView() {
    const table = mockServer.createTable()
    const database = { tables: [] }
    await testApp.store.dispatch('table/forceCreate', {
      database,
      data: table,
    })
    const view = mockServer.createGridView(database, table, {})
    return { table, view }
  }

  test('Modal with no view', async () => {
    const { table } = await givenThereIsATableWithView()
    const wrapper = await testApp.mount(ExportTableModal, {
      propsData: {
        table,
        view: null,
      },
    })
    await wrapper.vm.show()
    expect(wrapper.element).toMatchSnapshot()
    expect(wrapper.html()).toContain(`Export ${table.name}`)
    expect(wrapper.find('.select__item.active').html()).toContain(
      'exportEntireTable'
    )
  })

  test('Modal with view', async () => {
    const { table, view } = await givenThereIsATableWithView()
    const wrapper = await testApp.mount(ExportTableModal, {
      propsData: {
        table,
        view,
      },
    })
    await wrapper.vm.show()
    expect(wrapper.element).toMatchSnapshot()
    expect(wrapper.find('.select__item.active').html()).toContain(
      `${view.name}`
    )
  })
})
