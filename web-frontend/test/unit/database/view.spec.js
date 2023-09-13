import { TestApp } from '@baserow/test/helpers/testApp'
import Table from '@baserow/modules/database/pages/table'
import { utf8ByteSize } from '@baserow/modules/database/utils/view'

// Mock out debounce so we dont have to wait or simulate waiting for the various
// debounces in the search functionality.
jest.mock('lodash/debounce', () => jest.fn((fn) => fn))

describe('View Tests', () => {
  let testApp = null
  let mockServer = null

  beforeAll(() => {
    testApp = new TestApp()
    mockServer = testApp.mockServer
  })

  afterEach(() => testApp.afterEach())

  test('Default view is being set correctly initially', async () => {
    const { application, table, views } =
      await givenATableInTheServerWithMultipleViews()

    const gridView = views[0]
    const galleryView = views[1]

    // The first view is the Grid view, the Default view is the Gallery view which
    // is going to be rendered initially:
    const tableComponent = await testApp.mount(Table, {
      asyncDataParams: {
        databaseId: application.id,
        tableId: table.id,
        viewId: galleryView.id,
      },
    })

    const allCookies = testApp.store.$cookies
    const tableId = gridView.table_id

    // Check if Vuex store is updated correctly (first view):
    expect(testApp.store.getters['view/first'].id).toBe(gridView.id)
    // Check if cookie is updated correctly (default view):
    const cookieValue = allCookies.get('defaultViewId')
    expect(cookieValue.length).toBe(1)
    const defaultViewIdObject = cookieValue.find(
      (obj) => obj.table_id === tableId
    )
    expect(defaultViewIdObject.table_id).toBe(tableId)
    expect(defaultViewIdObject.id).toBe(galleryView.id)
    // Check if Vuex store is updated correctly (default view):
    expect(testApp.store.getters['view/defaultId']).toBe(galleryView.id)
    // Check if component is rendered:
    expect(tableComponent.find('div.gallery-view').exists()).toBe(true)
    expect(tableComponent.find('div.grid-view').exists()).toBe(false)
  })

  test('Default view is being set correctly after changing views', async () => {
    const { application, table, views } =
      await givenATableInTheServerWithMultipleViews()

    const gridView = views[0]
    const galleryView = views[1]

    // The first view is the Grid view, the Default view is the Gallery view which
    // is going to be rendered initially:
    const tableComponent = await testApp.mount(Table, {
      asyncDataParams: {
        databaseId: application.id,
        tableId: table.id,
        viewId: galleryView.id,
      },
    })

    const allCookies = testApp.store.$cookies
    const tableId = gridView.table_id

    // Check if Vuex store is updated correctly (first view):
    expect(testApp.store.getters['view/first'].id).toBe(gridView.id)
    // Check if cookie is updated correctly (default view):
    const cookieValue = allCookies.get('defaultViewId')
    expect(cookieValue.length).toBe(1)
    const defaultViewIdObject = cookieValue.find(
      (obj) => obj.table_id === tableId
    )
    expect(defaultViewIdObject.table_id).toBe(tableId)
    expect(defaultViewIdObject.id).toBe(galleryView.id)
    // Check if Vuex store is updated correctly (default view):
    expect(testApp.store.getters['view/defaultId']).toBe(galleryView.id)
    // Check if component is rendered:
    expect(tableComponent.find('div.gallery-view').exists()).toBe(true)
    expect(tableComponent.find('div.grid-view').exists()).toBe(false)

    // Let's switch back (select) the Grid (first) view:
    testApp.store.dispatch('view/selectById', gridView.id)

    // Check if Vuex store is updated correctly (first view):
    expect(testApp.store.getters['view/first'].id).toBe(gridView.id)
    // Check if cookie is updated correctly (default view):
    const updatedCookieValue = allCookies.get('defaultViewId')
    expect(updatedCookieValue.length).toBe(1)
    const updatedDefaultViewIdObject = updatedCookieValue.find(
      (obj) => obj.table_id === tableId
    )
    expect(updatedDefaultViewIdObject.table_id).toBe(tableId)
    expect(updatedDefaultViewIdObject.id).toBe(gridView.id)
    // Check if Vuex store is updated correctly (default view):
    expect(testApp.store.getters['view/defaultId']).toBe(gridView.id)
  })

  test('Default view is being set correctly after switching tables', async () => {
    const { application, tables, views } =
      await givenATableInTheServerWithMultipleTables()

    const firstTable = tables[0]
    const secondTable = tables[1]
    const firstTableGridView = views[0]
    const secondTableGridView = views[1]

    // The first (and default) view is the Grid view, which is going to be rendered
    // initially for the firstTable:
    const firstTableComponent = await testApp.mount(Table, {
      asyncDataParams: {
        databaseId: application.id,
        tableId: firstTable.id,
      },
    })

    const allCookies = testApp.store.$cookies

    // Check if Vuex store is updated correctly (first view):
    expect(testApp.store.getters['view/first'].id).toBe(firstTableGridView.id)
    // Check if cookie is updated correctly (default view):
    const cookieValue = allCookies.get('defaultViewId')
    expect(cookieValue.length).toBe(1)
    const defaultViewIdObject = cookieValue.find(
      (obj) => obj.table_id === firstTableGridView.table_id
    )
    expect(defaultViewIdObject.table_id).toBe(firstTableGridView.table_id)
    expect(defaultViewIdObject.id).toBe(firstTableGridView.id)
    // Check if Vuex store is updated correctly (default view):
    expect(testApp.store.getters['view/defaultId']).toBe(firstTableGridView.id)
    // Check if component is rendered:
    expect(firstTableComponent.find('div.grid-view').exists()).toBe(true)
    expect(firstTableComponent.find('div.gallery-view').exists()).toBe(false)

    // The first (and default) view is the Grid view, which is going to be rendered
    // initially for the secondTable:
    await testApp.mount(Table, {
      asyncDataParams: {
        databaseId: application.id,
        tableId: secondTable.id,
      },
    })

    // Let's switch to a different table in the database:
    testApp.store.dispatch('table/selectById', {
      databaseId: application.id,
      tableId: secondTable.id,
    })
    testApp.store.dispatch('view/selectById', secondTableGridView.id)

    const allCookiesAfterChangingTable = testApp.store.$cookies
    const cookieValueAfterChangingTable =
      allCookiesAfterChangingTable.get('defaultViewId')

    // Check if Vuex store is updated correctly (first view):
    expect(testApp.store.getters['view/first'].id).toBe(secondTableGridView.id)
    // Check if cookie is updated correctly (default view):
    expect(cookieValueAfterChangingTable.length).toBe(2)
    const defaultViewIdObjectAfterChangingTable =
      cookieValueAfterChangingTable.find(
        (obj) => obj.table_id === secondTableGridView.table_id
      )
    expect(defaultViewIdObjectAfterChangingTable.table_id).toBe(
      secondTableGridView.table_id
    )
    expect(defaultViewIdObjectAfterChangingTable.id).toBe(
      secondTableGridView.id
    )
    // Check if Vuex store is updated correctly (default view):
    expect(testApp.store.getters['view/defaultId']).toBe(secondTableGridView.id)
    // Check if component is rendered:
    expect(firstTableComponent.find('div.grid-view').exists()).toBe(true)
    expect(firstTableComponent.find('div.gallery-view').exists()).toBe(false)

    // Let's switch back to the first table in the database and see if first table's
    // default view is appended to the *end* of remembered views array:
    await testApp.mount(Table, {
      asyncDataParams: {
        databaseId: application.id,
        tableId: firstTable.id,
      },
    })
    testApp.store.dispatch('table/selectById', {
      databaseId: application.id,
      tableId: firstTable.id,
    })
    testApp.store.dispatch('view/selectById', firstTableGridView.id)

    const allCookiesAfterSwitchingBack = testApp.store.$cookies

    // Check if Vuex store is updated correctly (first view):
    expect(testApp.store.getters['view/first'].id).toBe(firstTableGridView.id)
    // Check if cookie is updated correctly (default view):
    const cookieValueAfterSwitchingBack =
      allCookiesAfterSwitchingBack.get('defaultViewId')
    expect(cookieValueAfterSwitchingBack.length).toBe(2)
    const defaultViewIdObjectAfterSwitchingBack =
      cookieValueAfterSwitchingBack.find(
        (obj) => obj.table_id === firstTableGridView.table_id
      )
    expect(defaultViewIdObjectAfterSwitchingBack.table_id).toBe(
      firstTableGridView.table_id
    )
    expect(defaultViewIdObjectAfterSwitchingBack.id).toBe(firstTableGridView.id)
    // Check if Vuex store is updated correctly (default view):
    expect(testApp.store.getters['view/defaultId']).toBe(firstTableGridView.id)

    expect(cookieValueAfterSwitchingBack[cookieValue.length - 1]).toMatchObject(
      defaultViewIdObjectAfterSwitchingBack
    )
  })

  test('Default view is being set correctly initially only from cookie', async () => {
    // set the cookie, render table without view id passed in, this should render
    // the default (Gallery) view
    const { application, table, views } =
      await givenATableInTheServerWithMultipleViews()

    const gridView = views[0]
    const galleryView = views[1]

    const tableId = gridView.table_id
    const allCookies = testApp.store.$cookies

    // Set the cookie for defaultView manually:
    const defaultViewIdData = []
    defaultViewIdData.push({
      table_id: galleryView.table_id,
      id: galleryView.id,
    })
    allCookies.set('defaultViewId', defaultViewIdData)

    // The first view is the Grid view, the Default view is the Gallery view,
    // we're not rendering any view initially and Default view (Gallery view)
    // should be picked up from the cookie
    const tableComponent = await testApp.mount(Table, {
      asyncDataParams: {
        databaseId: application.id,
        tableId: table.id,
      },
    })

    // Check if Vuex store is updated correctly (first view):
    expect(testApp.store.getters['view/first'].id).toBe(gridView.id)
    // Check if cookie is updated correctly (default view):
    const cookieValue = allCookies.get('defaultViewId')
    expect(cookieValue.length).toBe(1)
    const defaultViewIdObject = cookieValue.find(
      (obj) => obj.table_id === tableId
    )
    expect(defaultViewIdObject.table_id).toBe(tableId)
    expect(defaultViewIdObject.id).toBe(galleryView.id)
    // Check if Vuex store is updated correctly (default view):
    expect(testApp.store.getters['view/defaultId']).toBe(galleryView.id)
    // Check if component is rendered:
    expect(tableComponent.find('div.gallery-view').exists()).toBe(true)
    expect(tableComponent.find('div.grid-view').exists()).toBe(false)
  })

  test('Changing default view updates cookies array correctly', async () => {
    const { application, table, views } =
      await givenATableInTheServerWithMultipleViews()

    const gridView = views[0]

    const allCookies = testApp.store.$cookies

    // Calculate the size needed to exceed 4096 bytes
    const targetSize = 10000 // Choose a size greater than 4096

    // Generate random data to fill up the cookie
    const randomData = []
    let totalSize = 0
    let i = 0
    while (totalSize < targetSize) {
      const randomTableId = i++
      const randomViewId = i++
      const entry = { table_id: randomTableId, id: randomViewId }
      const entrySize = utf8ByteSize(encodeURIComponent(JSON.stringify(entry)))
      if (totalSize + entrySize <= targetSize) {
        randomData.push(entry)
        totalSize += entrySize
      } else {
        break
      }
    }
    allCookies.set('defaultViewId', randomData)
    const originalDataLength = randomData.length

    // Mount the component, which should update the cookies
    await testApp.mount(Table, {
      asyncDataParams: {
        databaseId: application.id,
        tableId: table.id,
        viewId: gridView.id,
      },
    })

    // The Default view is the Grid view and it should be set (appended) in the cookie
    const cookieValue = allCookies.get('defaultViewId')
    expect(cookieValue.length).toBeGreaterThan(0)

    const defaultViewIdObject = cookieValue.find(
      (obj) => obj.table_id === gridView.table_id
    )
    expect(defaultViewIdObject.table_id).toBe(gridView.table_id)
    expect(defaultViewIdObject.id).toBe(gridView.id)

    // Check if gridView is set as the last view in the array
    expect(cookieValue[cookieValue.length - 1]).toMatchObject(
      defaultViewIdObject
    )

    // Ensure that the first element is removed from the cookie array
    const updatedCookieValue = allCookies.get('defaultViewId')
    expect(updatedCookieValue).not.toContainEqual(randomData[0])
    expect(updatedCookieValue.length).toBeLessThan(originalDataLength)
  })

  async function givenATableInTheServerWithMultipleViews() {
    const table = mockServer.createTable()
    const { application } = await mockServer.createAppAndWorkspace(table)
    const gridView = mockServer.createGridView(application, table, {
      viewId: 1,
    })
    const galleryView = mockServer.createGalleryView(application, table, {
      viewId: 2,
    })

    mockServer.mock
      .onGet(`/database/views/table/${table.id}/`)
      .reply(200, [gridView, galleryView])

    const fields = mockServer.createFields(application, table, [
      {
        name: 'Name',
        type: 'text',
        primary: true,
      },
      {
        name: 'Last name',
        type: 'text',
      },
      {
        name: 'Notes',
        type: 'long_text',
      },
      {
        name: 'Active',
        type: 'boolean',
      },
    ])

    const rows = [
      {
        id: 1,
        order: 0,
        field_1: 'name',
        field_2: 'last_name',
        field_3: 'notes',
        field_4: false,
      },
    ]

    mockServer.createGridRows(gridView, fields, rows)
    mockServer.createFields(application, table, fields)
    mockServer.createGalleryRows(galleryView, fields, rows)

    const views = []
    views.push(gridView)
    views.push(galleryView)
    return { application, table, views }
  }

  async function givenATableInTheServerWithMultipleTables() {
    const firstTable = mockServer.createTable(1, 'Test Table 1')
    const secondTable = mockServer.createTable(2, 'Test Table 2')
    const { application } =
      await mockServer.createAppAndWorkspaceWithMultipleTables([
        firstTable,
        secondTable,
      ])

    // First table - 1 view:
    const firstTableGridView = mockServer.createGridView(
      application,
      firstTable,
      {
        viewId: 1,
      }
    )
    mockServer.mock
      .onGet(`/database/views/table/${firstTable.id}/`)
      .reply(200, [firstTableGridView])

    // Second table - 1 view:
    const secondTableGridView = mockServer.createGridView(
      application,
      secondTable,
      {
        viewId: 2,
      }
    )
    mockServer.mock
      .onGet(`/database/views/table/${secondTable.id}/`)
      .reply(200, [secondTableGridView])

    const fields = mockServer.createFields(application, firstTable, [
      {
        name: 'Name',
        type: 'text',
        primary: true,
      },
      {
        name: 'Last name',
        type: 'text',
      },
      {
        name: 'Notes',
        type: 'long_text',
      },
      {
        name: 'Active',
        type: 'boolean',
      },
    ])

    const rows = [
      {
        id: 1,
        order: 0,
        field_1: 'name',
        field_2: 'last_name',
        field_3: 'notes',
        field_4: false,
      },
    ]

    mockServer.createGridRows(firstTableGridView, fields, rows)
    mockServer.createGridRows(secondTableGridView, fields, rows)
    mockServer.createFields(application, firstTable, fields)
    mockServer.createFields(application, secondTable, fields)

    const views = []
    views.push(firstTableGridView)
    views.push(secondTableGridView)

    const tables = []
    tables.push(firstTable)
    tables.push(secondTable)
    return { application, tables, views }
  }
})
