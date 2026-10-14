import { TestApp } from '@baserow/test/helpers/testApp'
import GridViewFieldLinkRow from '@baserow/modules/database/components/view/grid/fields/GridViewFieldLinkRow'
import SelectRowModal from '@baserow/modules/database/components/row/SelectRowModal'

describe('GridViewFieldLinkRow component', () => {
  let testApp = null

  beforeEach(async () => {
    testApp = new TestApp()
    await testApp.store.dispatch('workspace/forceCreate', {
      id: 1,
      name: 'Workspace',
      users: [],
    })
    await testApp.store.dispatch('application/forceCreate', {
      id: 1,
      type: 'database',
      workspace: { id: 1 },
      tables: [
        { id: 10, name: 'Orders', database_id: 1 },
        { id: 11, name: 'Payments', database_id: 1 },
      ],
    })
    const database = testApp.store.getters['application/get'](1)
    const table = database.tables[0]
    testApp.store.commit('table/SET_SELECTED', { database, table })
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('a row created in the modal that already links back is not written again', async () => {
    const field = {
      id: 1,
      table_id: 10,
      type: 'link_row',
      link_row_table_id: 11,
      link_row_related_field_id: 21,
    }
    const wrapper = await testApp.mount(GridViewFieldLinkRow, {
      props: {
        field,
        value: [],
        row: { id: 7, order: '1.00' },
        selected: true,
        storePrefix: 'page/',
        workspaceId: 1,
      },
    })

    wrapper.findComponent(SelectRowModal).vm.$emit('selected', {
      row: {
        id: 99,
        order: '1.00',
        field_20: 'Payment',
        field_21: [{ id: 7 }],
      },
      primary: { id: 20, type: 'text' },
      created: true,
    })

    expect(wrapper.emitted('update')).toBeUndefined()
  })
})
