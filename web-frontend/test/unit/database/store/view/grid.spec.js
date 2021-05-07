import gridStore from '@baserow/modules/database/store/view/grid'
import { TestApp } from '@baserow/test/helpers/testApp'
import {
  EqualViewFilterType,
  ContainsViewFilterType,
} from '@baserow/modules/database/viewFilters'

describe('Grid view store', () => {
  let testApp = null
  let store = null

  beforeEach(() => {
    testApp = new TestApp()
    store = testApp.store
  })

  afterEach(() => {
    testApp.afterEach()
  })

  test('visibleByScrollTop', async () => {
    const state = Object.assign(gridStore.state(), {
      rowPadding: 1,
      bufferStartIndex: 0,
      bufferLimit: 9,
      bufferRequestSize: 3,
      rows: [
        { id: 1, order: '1.00' },
        { id: 2, order: '2.00' },
        { id: 3, order: '3.00' },
        { id: 4, order: '4.00' },
        { id: 5, order: '5.00' },
        { id: 6, order: '6.00' },
        { id: 7, order: '7.00' },
        { id: 8, order: '8.00' },
        { id: 9, order: '9.00' },
      ],
      count: 100,
      windowHeight: 99,
    })
    gridStore.state = () => state
    store.registerModule('grid', gridStore)

    await store.dispatch('grid/visibleByScrollTop', 0)
    expect(store.getters['grid/getRowsTop']).toBe(0)
    expect(store.getters['grid/getRowsStartIndex']).toBe(0)
    expect(store.getters['grid/getRowsEndIndex']).toBe(3)

    await store.dispatch('grid/visibleByScrollTop', 10)
    expect(store.getters['grid/getRowsTop']).toBe(0)
    expect(store.getters['grid/getRowsStartIndex']).toBe(0)
    expect(store.getters['grid/getRowsEndIndex']).toBe(3)

    await store.dispatch('grid/visibleByScrollTop', 33)
    expect(store.getters['grid/getRowsTop']).toBe(33)
    expect(store.getters['grid/getRowsStartIndex']).toBe(1)
    expect(store.getters['grid/getRowsEndIndex']).toBe(4)

    await store.dispatch('grid/visibleByScrollTop', 66)
    expect(store.getters['grid/getRowsTop']).toBe(66)
    expect(store.getters['grid/getRowsStartIndex']).toBe(2)
    expect(store.getters['grid/getRowsEndIndex']).toBe(5)

    await store.dispatch('grid/visibleByScrollTop', 396)
    expect(store.getters['grid/getRowsTop']).toBe(297)
    expect(store.getters['grid/getRowsStartIndex']).toBe(9)
    expect(store.getters['grid/getRowsEndIndex']).toBe(9)

    store.state.grid.bufferStartIndex = 9
    store.state.grid.rows = [
      { id: 10, order: '10.00' },
      { id: 11, order: '11.00' },
      { id: 12, order: '12.00' },
      { id: 13, order: '13.00' },
      { id: 14, order: '14.00' },
      { id: 15, order: '15.00' },
      { id: 16, order: '16.00' },
      { id: 17, order: '17.00' },
      { id: 18, order: '18.00' },
    ]

    await store.dispatch('grid/visibleByScrollTop', 396)
    expect(store.getters['grid/getRowsTop']).toBe(396)
    expect(store.getters['grid/getRowsStartIndex']).toBe(3)
    expect(store.getters['grid/getRowsEndIndex']).toBe(6)
  })

  test('createdNewRow', async () => {
    const state = Object.assign(gridStore.state(), {
      bufferStartIndex: 0,
      bufferLimit: 6,
      rows: [
        { id: 2, order: '2.00000000000000000000' },
        { id: 3, order: '3.00000000000000000000' },
        { id: 4, order: '4.00000000000000000000' },
        { id: 5, order: '5.00000000000000000000' },
        { id: 6, order: '6.00000000000000000000' },
        { id: 7, order: '7.00000000000000000000' },
      ],
      count: 100,
    })
    gridStore.state = () => state
    store.registerModule('grid', gridStore)

    const view = {
      filters: [],
      sortings: [],
    }
    const fields = []
    const primary = {}
    const getScrollTop = () => 0

    await store.dispatch('grid/createdNewRow', {
      view,
      fields,
      primary,
      values: { id: 1, order: '1.00000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(7)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(7)
    expect(store.getters['grid/getCount']).toBe(101)

    await store.dispatch('grid/createdNewRow', {
      view,
      fields,
      primary,
      values: { id: 8, order: '4.50000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(8)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][4].id).toBe(8)
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(8)
    expect(store.getters['grid/getCount']).toBe(102)

    await store.dispatch('grid/createdNewRow', {
      view,
      fields,
      primary,
      values: { id: 102, order: '102.00000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(8)
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(8)
    expect(store.getters['grid/getCount']).toBe(103)

    store.state.grid.bufferStartIndex = 9
    store.state.grid.bufferLimit = 6
    store.state.grid.rows = [
      { id: 10, order: '10.00000000000000000000' },
      { id: 11, order: '11.00000000000000000000' },
      { id: 12, order: '12.00000000000000000000' },
      { id: 13, order: '13.00000000000000000000' },
      { id: 14, order: '14.00000000000000000000' },
      { id: 15, order: '15.00000000000000000000' },
    ]

    await store.dispatch('grid/createdNewRow', {
      view,
      fields,
      primary,
      values: { id: 2, order: '2.00000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(6)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getBufferStartIndex']).toBe(10)
    expect(store.getters['grid/getBufferLimit']).toBe(6)
    expect(store.getters['grid/getCount']).toBe(104)

    // When creating a new row that does not match the filters we don't expect
    // anything to happen because the row does not belong on that view.
    await store.dispatch('grid/createdNewRow', {
      view: {
        id: 1,
        filters_disabled: false,
        filter_type: 'AND',
        filters: [
          {
            id: 1,
            view: 1,
            field: 1,
            type: EqualViewFilterType.getType(),
            value: 'not_matching',
          },
        ],
        sortings: [],
      },
      fields,
      primary: {
        id: 1,
        name: 'Test 1',
        type: 'text',
        primary: true,
      },
      values: { id: 16, order: '11.50000000000000000000', field_1: 'value' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(6)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][1].id).toBe(11)
    expect(store.getters['grid/getAllRows'][2].id).toBe(12)
    expect(store.getters['grid/getAllRows'][3].id).toBe(13)
    expect(store.getters['grid/getAllRows'][4].id).toBe(14)
    expect(store.getters['grid/getAllRows'][5].id).toBe(15)
    expect(store.getters['grid/getBufferStartIndex']).toBe(10)
    expect(store.getters['grid/getBufferLimit']).toBe(6)
    expect(store.getters['grid/getCount']).toBe(104)
  })

  test('updatedExistingRow', async () => {
    const state = Object.assign(gridStore.state(), {
      bufferStartIndex: 0,
      bufferLimit: 3,
      rows: [
        { id: 1, order: '1.00000000000000000000', field_1: 'Value 1' },
        {
          id: 2,
          order: '2.00000000000000000000',
          field_1: 'Value 2',
          _: { mustPersist: true },
        },
        { id: 3, order: '3.00000000000000000000', field_1: 'Value 3' },
      ],
      count: 3,
    })
    gridStore.state = () => state
    store.registerModule('grid', gridStore)

    const view = {
      id: 1,
      filters_disabled: false,
      filter_type: 'AND',
      filters: [
        {
          id: 1,
          view: 1,
          field: 1,
          type: ContainsViewFilterType.getType(),
          value: 'value',
        },
      ],
      sortings: [],
    }
    const fields = []
    const primary = {
      id: 1,
      name: 'Test 1',
      type: 'text',
      primary: true,
    }
    const getScrollTop = () => 0

    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: { id: 2, order: '2.00000000000000000000', field_1: 'Value 2' },
      values: { field_1: 'Value 2 updated' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(3)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 1')
    expect(store.getters['grid/getAllRows'][1].id).toBe(2)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 2 updated')
    expect(store.getters['grid/getAllRows'][1]._.mustPersist).toBe(true)
    expect(store.getters['grid/getAllRows'][2].id).toBe(3)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 3')
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(3)
    expect(store.getters['grid/getCount']).toBe(3)

    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: { id: 1, order: '1.00000000000000000000', field_1: 'Value 1' },
      values: { field_1: 'Value 1 updated' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(3)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 1 updated')
    expect(store.getters['grid/getAllRows'][1].id).toBe(2)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 2 updated')
    expect(store.getters['grid/getAllRows'][2].id).toBe(3)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 3')
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(3)
    expect(store.getters['grid/getCount']).toBe(3)

    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: { id: 3, order: '3.00000000000000000000', field_1: 'Value 3' },
      values: { field_1: 'Value 3 updated' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(3)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 1 updated')
    expect(store.getters['grid/getAllRows'][1].id).toBe(2)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 2 updated')
    expect(store.getters['grid/getAllRows'][2].id).toBe(3)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 3 updated')
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(3)
    expect(store.getters['grid/getCount']).toBe(3)

    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: { id: 4, order: '4.00000000000000000000', field_1: 'empty' },
      values: { field_1: 'Value 4 updated' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(4)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 1 updated')
    expect(store.getters['grid/getAllRows'][1].id).toBe(2)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 2 updated')
    expect(store.getters['grid/getAllRows'][2].id).toBe(3)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 3 updated')
    expect(store.getters['grid/getAllRows'][3].id).toBe(4)
    expect(store.getters['grid/getAllRows'][3].field_1).toBe('Value 4 updated')
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(4)
    expect(store.getters['grid/getCount']).toBe(4)

    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: {
        id: 4,
        order: '4.00000000000000000000',
        field_1: 'Value 4 updated',
      },
      values: { field_1: 'empty' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(3)
    expect(store.getters['grid/getAllRows'][0].id).toBe(1)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 1 updated')
    expect(store.getters['grid/getAllRows'][1].id).toBe(2)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 2 updated')
    expect(store.getters['grid/getAllRows'][2].id).toBe(3)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 3 updated')
    expect(store.getters['grid/getBufferStartIndex']).toBe(0)
    expect(store.getters['grid/getBufferLimit']).toBe(3)
    expect(store.getters['grid/getCount']).toBe(3)

    store.state.grid.bufferStartIndex = 9
    store.state.grid.bufferLimit = 6
    store.state.grid.rows = [
      { id: 10, order: '10.00000000000000000000', field_1: 'Value 10' },
      { id: 11, order: '11.00000000000000000000', field_1: 'Value 11' },
      { id: 12, order: '12.00000000000000000000', field_1: 'Value 12' },
      { id: 13, order: '13.00000000000000000000', field_1: 'Value 13' },
      { id: 14, order: '14.00000000000000000000', field_1: 'Value 14' },
      { id: 15, order: '15.00000000000000000000', field_1: 'Value 15' },
    ]
    store.state.grid.count = 100

    // Change the first row in the buffer. We expect it to be removed from the
    // buffer because aren't 100% sure it still belongs in the buffer.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: { id: 10, order: '10.00000000000000000000', field_1: 'Value 10' },
      values: { field_1: 'Value 10 updated' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(5)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(12)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 12')
    expect(store.getters['grid/getAllRows'][2].id).toBe(13)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 13')
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][3].field_1).toBe('Value 14')
    expect(store.getters['grid/getAllRows'][4].id).toBe(15)
    expect(store.getters['grid/getAllRows'][4].field_1).toBe('Value 15')
    expect(store.getters['grid/getBufferStartIndex']).toBe(10)
    expect(store.getters['grid/getBufferLimit']).toBe(5)
    expect(store.getters['grid/getCount']).toBe(100)

    // Change the last row in the buffer. We expect it to be deleted from the buffer
    // because it we aren't 100% sure it still belongs in the buffer.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: { id: 15, order: '15.00000000000000000000', field_1: 'Value 15' },
      values: { field_1: 'Value 15 updated' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(4)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(12)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 12')
    expect(store.getters['grid/getAllRows'][2].id).toBe(13)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 13')
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][3].field_1).toBe('Value 14')
    expect(store.getters['grid/getBufferStartIndex']).toBe(10)
    expect(store.getters['grid/getBufferLimit']).toBe(4)
    expect(store.getters['grid/getCount']).toBe(100)

    // Move a row in the buffer to another position in the buffer.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: { id: 12, order: '12.00000000000000000000', field_1: 'Value 12' },
      values: {
        order: '13.50000000000000000000',
        field_1: 'Value 13.5',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(4)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(13)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 13')
    expect(store.getters['grid/getAllRows'][2].id).toBe(12)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 13.5')
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][3].field_1).toBe('Value 14')
    expect(store.getters['grid/getBufferStartIndex']).toBe(10)
    expect(store.getters['grid/getBufferLimit']).toBe(4)
    expect(store.getters['grid/getCount']).toBe(100)

    // Move an existing row before the buffer. We expect the row to be removed from
    // the buffer because we can't be 100% sure it still belongs in there.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: {
        id: 12,
        order: '13.50000000000000000000',
        field_1: 'Value 13.5',
      },
      values: {
        order: '2.99999999999999999999',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(3)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(13)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 13')
    expect(store.getters['grid/getAllRows'][2].id).toBe(14)
    expect(store.getters['grid/getAllRows'][2].field_1).toBe('Value 14')
    expect(store.getters['grid/getBufferStartIndex']).toBe(11)
    expect(store.getters['grid/getBufferLimit']).toBe(3)
    expect(store.getters['grid/getCount']).toBe(100)

    // Move an existing row before the buffer. We expect the row to be removed from
    // the buffer because we can't be 100% sure it still belongs in there.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: {
        id: 13,
        order: '13.00000000000000000000',
        field_1: 'Value 13',
      },
      values: {
        order: '16.99999999999999999999',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(2)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(14)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 14')
    expect(store.getters['grid/getBufferStartIndex']).toBe(11)
    expect(store.getters['grid/getBufferLimit']).toBe(2)
    expect(store.getters['grid/getCount']).toBe(100)

    // Move a row that is not in the buffer from before to after.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: {
        id: 2,
        order: '2.00000000000000000000',
        field_1: 'Value 2',
      },
      values: {
        order: '20.99999999999999999999',
        field_2: 'Value 20',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(2)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(14)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 14')
    expect(store.getters['grid/getBufferStartIndex']).toBe(10)
    expect(store.getters['grid/getBufferLimit']).toBe(2)
    expect(store.getters['grid/getCount']).toBe(100)

    // Move a row that is not in the buffer from before to after.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: {
        id: 2,
        order: '20.99999999999999999999',
        field_1: 'Value 20',
      },
      values: {
        order: '2.99999999999999999999',
        field_2: 'Value 20',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(2)
    expect(store.getters['grid/getAllRows'][0].id).toBe(11)
    expect(store.getters['grid/getAllRows'][0].field_1).toBe('Value 11')
    expect(store.getters['grid/getAllRows'][1].id).toBe(14)
    expect(store.getters['grid/getAllRows'][1].field_1).toBe('Value 14')
    expect(store.getters['grid/getBufferStartIndex']).toBe(11)
    expect(store.getters['grid/getBufferLimit']).toBe(2)
    expect(store.getters['grid/getCount']).toBe(100)

    store.state.grid.bufferStartIndex = 9
    store.state.grid.bufferLimit = 6
    store.state.grid.rows = [
      { id: 10, order: '14.99999999999999999995', field_1: 'Value 10' },
      { id: 11, order: '14.99999999999999999996', field_1: 'Value 11' },
      { id: 12, order: '14.99999999999999999997', field_1: 'Value 12' },
      { id: 13, order: '14.99999999999999999998', field_1: 'Value 13' },
      { id: 14, order: '14.99999999999999999999', field_1: 'Value 14' },
      { id: 15, order: '15.00000000000000000000', field_1: 'Value 15' },
    ]
    store.state.grid.count = 100

    // Move the row to an order that already exists, which means all the order lower
    // than the new order should be decreased by 0.00000000000000000001.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: {
        id: 11,
        order: '14.99999999999999999996',
        field_1: 'Value 11',
      },
      values: {
        order: '14.99999999999999999999',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(6)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][0].order).toBe(
      '14.99999999999999999994'
    )
    expect(store.getters['grid/getAllRows'][1].id).toBe(12)
    expect(store.getters['grid/getAllRows'][1].order).toBe(
      '14.99999999999999999996'
    )
    expect(store.getters['grid/getAllRows'][2].id).toBe(13)
    expect(store.getters['grid/getAllRows'][2].order).toBe(
      '14.99999999999999999997'
    )
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][3].order).toBe(
      '14.99999999999999999998'
    )
    expect(store.getters['grid/getAllRows'][4].id).toBe(11)
    expect(store.getters['grid/getAllRows'][4].order).toBe(
      '14.99999999999999999999'
    )
    expect(store.getters['grid/getAllRows'][5].id).toBe(15)
    expect(store.getters['grid/getAllRows'][5].order).toBe(
      '15.00000000000000000000'
    )
    expect(store.getters['grid/getBufferStartIndex']).toBe(9)
    expect(store.getters['grid/getBufferLimit']).toBe(6)
    expect(store.getters['grid/getCount']).toBe(100)

    // If only a field value is updated then there the other row order don't have to be
    // decreased.
    await store.dispatch('grid/updatedExistingRow', {
      view,
      fields,
      primary,
      row: {
        id: 11,
        order: '14.99999999999999999999',
        field_1: 'Value 11',
      },
      values: {
        field_1: 'Value 11.1',
      },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(6)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][0].order).toBe(
      '14.99999999999999999994'
    )
    expect(store.getters['grid/getAllRows'][1].id).toBe(12)
    expect(store.getters['grid/getAllRows'][1].order).toBe(
      '14.99999999999999999996'
    )
    expect(store.getters['grid/getAllRows'][2].id).toBe(13)
    expect(store.getters['grid/getAllRows'][2].order).toBe(
      '14.99999999999999999997'
    )
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][3].order).toBe(
      '14.99999999999999999998'
    )
    expect(store.getters['grid/getAllRows'][4].id).toBe(11)
    expect(store.getters['grid/getAllRows'][4].order).toBe(
      '14.99999999999999999999'
    )
    expect(store.getters['grid/getAllRows'][5].id).toBe(15)
    expect(store.getters['grid/getAllRows'][5].order).toBe(
      '15.00000000000000000000'
    )
    expect(store.getters['grid/getBufferStartIndex']).toBe(9)
    expect(store.getters['grid/getBufferLimit']).toBe(6)
    expect(store.getters['grid/getCount']).toBe(100)
  })

  test('deletedExistingRow', async () => {
    const state = Object.assign(gridStore.state(), {
      bufferStartIndex: 9,
      bufferLimit: 6,
      rows: [
        { id: 10, order: '10.00000000000000000000' },
        { id: 11, order: '11.00000000000000000000' },
        { id: 12, order: '12.00000000000000000000' },
        { id: 13, order: '13.00000000000000000000' },
        { id: 14, order: '14.00000000000000000000' },
        { id: 15, order: '15.00000000000000000000' },
      ],
      count: 100,
    })
    gridStore.state = () => state
    store.registerModule('grid', gridStore)

    const view = {
      filters: [],
      sortings: [],
    }
    const fields = []
    const primary = {}
    const getScrollTop = () => 0

    await store.dispatch('grid/deletedExistingRow', {
      view,
      fields,
      primary,
      row: { id: 3, order: '3.00000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(6)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][1].id).toBe(11)
    expect(store.getters['grid/getAllRows'][2].id).toBe(12)
    expect(store.getters['grid/getAllRows'][3].id).toBe(13)
    expect(store.getters['grid/getAllRows'][4].id).toBe(14)
    expect(store.getters['grid/getAllRows'][5].id).toBe(15)
    expect(store.getters['grid/getBufferStartIndex']).toBe(8)
    expect(store.getters['grid/getBufferLimit']).toBe(6)
    expect(store.getters['grid/getCount']).toBe(99)

    await store.dispatch('grid/deletedExistingRow', {
      view,
      fields,
      primary,
      row: { id: 20, order: '20.00000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(6)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][1].id).toBe(11)
    expect(store.getters['grid/getAllRows'][2].id).toBe(12)
    expect(store.getters['grid/getAllRows'][3].id).toBe(13)
    expect(store.getters['grid/getAllRows'][4].id).toBe(14)
    expect(store.getters['grid/getAllRows'][5].id).toBe(15)
    expect(store.getters['grid/getBufferStartIndex']).toBe(8)
    expect(store.getters['grid/getBufferLimit']).toBe(6)
    expect(store.getters['grid/getCount']).toBe(98)

    await store.dispatch('grid/deletedExistingRow', {
      view,
      fields,
      primary,
      row: { id: 13, order: '13.00000000000000000000' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(5)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][1].id).toBe(11)
    expect(store.getters['grid/getAllRows'][2].id).toBe(12)
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][4].id).toBe(15)
    expect(store.getters['grid/getBufferStartIndex']).toBe(8)
    expect(store.getters['grid/getBufferLimit']).toBe(5)
    expect(store.getters['grid/getCount']).toBe(97)

    // When deleting a new row that does not match the filters we don't expect
    // anything to happen because the row does not belong on that view.
    await store.dispatch('grid/deletedExistingRow', {
      view: {
        id: 1,
        filters_disabled: false,
        filter_type: 'AND',
        filters: [
          {
            id: 1,
            view: 1,
            field: 1,
            type: EqualViewFilterType.getType(),
            value: 'not_matching',
          },
        ],
        sortings: [],
      },
      fields,
      primary: {
        id: 1,
        name: 'Test 1',
        type: 'text',
        primary: true,
      },
      row: { id: 16, order: '11.50000000000000000000', field_1: 'value' },
      getScrollTop,
    })
    expect(store.getters['grid/getAllRows'].length).toBe(5)
    expect(store.getters['grid/getAllRows'][0].id).toBe(10)
    expect(store.getters['grid/getAllRows'][1].id).toBe(11)
    expect(store.getters['grid/getAllRows'][2].id).toBe(12)
    expect(store.getters['grid/getAllRows'][3].id).toBe(14)
    expect(store.getters['grid/getAllRows'][4].id).toBe(15)
    expect(store.getters['grid/getBufferStartIndex']).toBe(8)
    expect(store.getters['grid/getBufferLimit']).toBe(5)
    expect(store.getters['grid/getCount']).toBe(97)
  })
})
