import { TestApp } from '@baserow/test/helpers/testApp'
import RowEditFieldLinkRow from '@baserow/modules/database/components/row/RowEditFieldLinkRow'
import SelectRowModal from '@baserow/modules/database/components/row/SelectRowModal'

const WORKSPACE_ID = 1
const ORDERS_TABLE_ID = 10
const CUSTOMERS_TABLE_ID = 11
const RELATED_FIELD_ID = 21
const CUSTOMER_ROW_ID = 7

// The customer's "Orders" field, as shown in the foreign row modal opened from Orders.
const field = {
  id: 1,
  table_id: CUSTOMERS_TABLE_ID,
  name: 'Orders',
  order: 0,
  type: 'link_row',
  primary: false,
  link_row_table_id: ORDERS_TABLE_ID,
  link_row_related_field_id: RELATED_FIELD_ID,
  link_row_limit_selection_view_id: null,
  link_row_multiple_relationships: true,
  _: { loading: false },
}

const ordersPrimary = {
  id: 20,
  table_id: ORDERS_TABLE_ID,
  name: 'Name',
  order: 0,
  type: 'text',
  primary: true,
  text_default: '',
  _: { loading: false },
}

const createdOrder = {
  id: 99,
  order: '1.00000000000000000000',
  [`field_${ordersPrimary.id}`]: 'Order 1',
  [`field_${RELATED_FIELD_ID}`]: [{ id: CUSTOMER_ROW_ID, value: 'Customer' }],
}

describe('RowEditFieldLinkRow component', () => {
  let testApp = null

  beforeEach(async () => {
    testApp = new TestApp()
    await testApp.store.dispatch('workspace/forceCreate', {
      id: WORKSPACE_ID,
      name: 'Workspace',
      users: [],
    })
    await testApp.store.dispatch('application/forceCreate', {
      id: 1,
      type: 'database',
      workspace: { id: WORKSPACE_ID },
      tables: [
        { id: ORDERS_TABLE_ID, name: 'Orders', database_id: 1 },
        { id: CUSTOMERS_TABLE_ID, name: 'Customers', database_id: 1 },
      ],
    })
    const database = testApp.store.getters['application/get'](1)
    testApp.store.commit('table/SET_SELECTED', {
      database,
      table: database.tables.find(({ id }) => id === ORDERS_TABLE_ID),
    })
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('a row created from a foreign row is written, realtime would not bring it', async () => {
    const wrapper = await testApp.mount(RowEditFieldLinkRow, {
      props: {
        field,
        value: [],
        row: { id: CUSTOMER_ROW_ID, order: '1.00000000000000000000' },
        readOnly: false,
        workspaceId: WORKSPACE_ID,
      },
    })

    wrapper.findComponent(SelectRowModal).vm.$emit('selected', {
      row: createdOrder,
      primary: ordersPrimary,
      fields: [],
      created: true,
    })

    expect(wrapper.emitted('update')).toEqual([
      [[{ id: 99, value: 'Order 1', order: '1.00000000000000000000' }], []],
    ])
  })
})
