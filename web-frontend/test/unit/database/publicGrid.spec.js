import { TestApp } from '@baserow/test/helpers/testApp'
import PublicGrid from '@baserow/modules/database/pages/publicGridView'

// Mock out debounce so we dont have to wait or simulate waiting for the various
// debounces in the search functionality.
jest.mock('lodash/debounce', () => jest.fn((fn) => fn))

describe('Public View Page Tests', () => {
  let testApp = null
  let mockServer = null

  beforeAll(() => {
    testApp = new TestApp()
    mockServer = testApp.mockServer
  })

  afterEach(() => testApp.afterEach())

  test('Can see a publicly shared grid view', async () => {
    const slug = 'testSlug'
    const gridViewName = 'my public grid view name'
    givenAPubliclySharedGridViewWithSlug(gridViewName, slug)

    const publicGridViewPage = await testApp.mount(PublicGrid, {
      asyncDataParams: {
        slug,
      },
    })

    expect(publicGridViewPage.html()).toContain(gridViewName)
    expect(publicGridViewPage.element).toMatchSnapshot()
  })

  function givenAPubliclySharedGridViewWithSlug(name, slug) {
    const fields = [
      {
        id: 0,
        name: 'Name',
        type: 'text',
        primary: true,
      },
      {
        id: 1,
        name: 'Last name',
        type: 'text',
      },
      {
        id: 2,
        name: 'Notes',
        type: 'long_text',
      },
      {
        id: 3,
        name: 'Active',
        type: 'boolean',
      },
    ]
    const gridView = mockServer.createPublicGridView(slug, {
      name,
      fields,
    })
    mockServer.createPublicGridViewRows(slug, fields, [
      {
        id: 1,
        order: 0,
        field_1: 'name',
        field_2: 'last_name',
        field_3: 'notes',
        field_4: false,
      },
    ])

    return { gridView }
  }
})
