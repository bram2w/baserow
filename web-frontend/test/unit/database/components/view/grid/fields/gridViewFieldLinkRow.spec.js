import { TestApp } from '@baserow/test/helpers/testApp'
import GridViewFieldLinkRow from '@baserow/modules/database/components/view/grid/fields/GridViewFieldLinkRow'
import SelectRowModal from '@baserow/modules/database/components/row/SelectRowModal'

const WORKSPACE_ID = 1
const TABLE_ID = 10
const LINKED_TABLE_ID = 11
const RELATED_FIELD_ID = 21
const ROW_ID = 7

const field = {
  id: 1,
  table_id: TABLE_ID,
  name: 'Payments',
  order: 0,
  type: 'link_row',
  primary: false,
  link_row_table_id: LINKED_TABLE_ID,
  link_row_related_field_id: RELATED_FIELD_ID,
  link_row_limit_selection_view_id: null,
  link_row_multiple_relationships: true,
  _: { loading: false },
}

const linkedPrimary = {
  id: 20,
  table_id: LINKED_TABLE_ID,
  name: 'Name',
  order: 0,
  type: 'text',
  primary: true,
  text_default: '',
  _: { loading: false },
}

const linkedRow = (linksBack) => ({
  id: 99,
  order: '1.00000000000000000000',
  [`field_${linkedPrimary.id}`]: 'Payment 1',
  [`field_${RELATED_FIELD_ID}`]: linksBack
    ? [{ id: ROW_ID, value: 'Order 1' }]
    : [],
})

describe('GridViewFieldLinkRow component', () => {
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
        { id: TABLE_ID, name: 'Orders', database_id: 1 },
        { id: LINKED_TABLE_ID, name: 'Payments', database_id: 1 },
      ],
    })
  })

  const openTable = (tableId) => {
    const database = testApp.store.getters['application/get'](1)
    const table = database.tables.find(({ id }) => id === tableId)
    testApp.store.commit('table/SET_SELECTED', { database, table })
  }

  afterEach(async () => {
    await testApp.afterEach()
  })

  const mountComponent = () =>
    testApp.mount(GridViewFieldLinkRow, {
      props: {
        field,
        value: [],
        row: { id: ROW_ID, order: '1.00000000000000000000' },
        readOnly: false,
        selected: true,
        storePrefix: 'page/',
        workspaceId: WORKSPACE_ID,
      },
    })

  const selectInModal = (wrapper, payload) =>
    wrapper.findComponent(SelectRowModal).vm.$emit('selected', {
      primary: linkedPrimary,
      fields: [],
      ...payload,
    })

  test('a row created in the modal that already links back is not written again', async () => {
    openTable(TABLE_ID)
    const wrapper = await mountComponent()

    await selectInModal(wrapper, { row: linkedRow(true), created: true })

    expect(wrapper.emitted('update')).toBeUndefined()
  })

  test('a row created in the modal without the link back is added', async () => {
    openTable(TABLE_ID)
    const wrapper = await mountComponent()

    await selectInModal(wrapper, { row: linkedRow(false), created: true })

    expect(wrapper.emitted('update')).toEqual([
      [[{ id: 99, value: 'Payment 1', order: '1.00000000000000000000' }], []],
    ])
  })

  test('a row created with the link back is added when its table is not open', async () => {
    // The realtime update of a row outside the open table never reaches this tab.
    openTable(LINKED_TABLE_ID)
    const wrapper = await mountComponent()

    await selectInModal(wrapper, { row: linkedRow(true), created: true })

    expect(wrapper.emitted('update')).toEqual([
      [[{ id: 99, value: 'Payment 1', order: '1.00000000000000000000' }], []],
    ])
  })

  test('a listed row is added even if its loaded values still link back', async () => {
    openTable(TABLE_ID)
    const wrapper = await mountComponent()

    // The modal's list isn't refetched after unlinking, so its values can be stale.
    await selectInModal(wrapper, { row: linkedRow(true) })

    expect(wrapper.emitted('update')).toEqual([
      [[{ id: 99, value: 'Payment 1', order: '1.00000000000000000000' }], []],
    ])
  })
})
