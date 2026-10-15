import { TestApp } from '@baserow/test/helpers/testApp'
import { DATA_SCOPES } from '@baserow/modules/builder/constants'
import TableElement from '@baserow/modules/builder/components/elements/components/TableElement'
import RecordSelectorElement from '@baserow/modules/builder/components/elements/components/RecordSelectorElement'

describe('Builder data provider types', () => {
  let testApp = null

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('previous action provider resolves list workflow action results', () => {
    const dataProvider = testApp
      .getRegistry()
      .get('builderDataProvider', 'previous_action')

    const workflowAction = {
      id: 10,
      type: 'csv_file_reader',
      service: {
        id: 20,
        type: 'csv_file_reader',
        schema: {
          items: {
            properties: {
              Email: { title: 'Email' },
            },
          },
        },
      },
    }
    const page = { id: 1, workflowActions: [workflowAction] }
    const applicationContext = {
      page,
      previousActionResults: {
        10: {
          results: [{ Email: 'a@example.com' }, { Email: 'b@example.com' }],
          has_next_page: false,
        },
      },
    }

    expect(dataProvider.getDataChunk(applicationContext, ['10'])).toEqual([
      { Email: 'a@example.com' },
      { Email: 'b@example.com' },
    ])
    expect(dataProvider.getDataChunk(applicationContext, ['10', '1'])).toEqual({
      Email: 'b@example.com',
    })
    expect(
      dataProvider.getDataChunk(applicationContext, ['10', '*', 'Email'])
    ).toEqual(['a@example.com', 'b@example.com'])
  })

  test('previous action provider exposes list workflow action schemas', () => {
    const dataProvider = testApp
      .getRegistry()
      .get('builderDataProvider', 'previous_action')

    const previousWorkflowAction = {
      id: 10,
      type: 'csv_file_reader',
      event: 'click',
      element_id: 100,
      order: 1,
      service: {
        id: 20,
        type: 'csv_file_reader',
        schema: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              Email: { title: 'Email', type: 'string' },
            },
          },
        },
      },
    }
    const currentWorkflowAction = {
      id: 11,
      type: 'notification',
      event: 'click',
      element_id: 100,
      order: 2,
    }
    const page = {
      id: 1,
      workflowActions: [previousWorkflowAction, currentWorkflowAction],
    }
    const applicationContext = {
      page,
      element: { id: 100 },
      workflowAction: currentWorkflowAction,
    }

    expect(dataProvider.getDataSchema(applicationContext)).toEqual({
      type: 'object',
      properties: {
        10: {
          title: 'serviceType.coreCSVFileReader ',
          type: 'array',
          items: {
            type: 'object',
            properties: {
              Email: { title: 'Email', type: 'string' },
            },
          },
        },
      },
    })
  })

  const formContainerPage = () => {
    const formContainer = {
      id: 2,
      type: 'form_container',
      page_id: 1,
      _: { elementNamespacePath: [] },
    }
    const nameInput = {
      id: 3,
      type: 'input_text',
      page_id: 1,
      _: { elementNamespacePath: [] },
      label: { formula: "'Name'" },
      default_value: { formula: '' },
      placeholder: { formula: '' },
    }
    const emailInput = {
      id: 4,
      type: 'input_text',
      page_id: 1,
      _: { elementNamespacePath: [] },
      label: { formula: "'Email'" },
      default_value: { formula: '' },
      placeholder: { formula: '' },
    }
    const page = {
      id: 1,
      elementMap: { 2: formContainer, 3: nameInput, 4: emailInput },
      orderedElements: [formContainer, nameInput, emailInput],
      graph: {
        0: 2,
        2: { children: { '': [3] } },
        3: { next: { '': [4] } },
        4: {},
      },
      formData: {
        3: { value: 'Ada', isValid: true, touched: true },
        4: { value: 'ada@example.com', isValid: true, touched: true },
      },
    }
    return {
      builder: { id: 1 },
      workspace: {},
      page,
      element: formContainer,
    }
  }

  test('form data provider dispatches the inputs of a submitted form', () => {
    const dataProvider = testApp
      .getRegistry()
      .get('builderDataProvider', 'form_data')
    const applicationContext = formContainerPage()

    expect(dataProvider.getDataContent(applicationContext)).toEqual({
      3: 'Ada',
      4: 'ada@example.com',
    })
    expect(dataProvider.getActionDispatchContext(applicationContext)).toEqual([
      { 3: 'Ada', 4: 'ada@example.com' },
      {},
    ])
  })

  test('form data provider applies its requested data scope', () => {
    const dataProvider = testApp
      .getRegistry()
      .get('builderDataProvider', 'form_data')
    const applicationContext = formContainerPage()
    const excludingTargetSubtreeContext = {
      ...applicationContext,
      dataScope: DATA_SCOPES.EXCLUDE_TARGET_SUBTREE,
    }

    expect(dataProvider.isValid(['3'])).toBe(true)
    expect(dataProvider.isValid(['3'], applicationContext)).toBe(true)
    expect(dataProvider.isValid(['3'], excludingTargetSubtreeContext)).toBe(
      false
    )
    expect(
      Object.keys(dataProvider.getDataSchema(applicationContext).properties)
    ).toEqual(['3', '4'])
    expect(
      dataProvider.getDataSchema(excludingTargetSubtreeContext).properties
    ).toEqual({})
  })

  test('current record dispatch preserves nested row indexes', () => {
    const dataProvider = testApp
      .getRegistry()
      .get('builderDataProvider', 'current_record')

    expect(
      dataProvider.getActionDispatchContext({
        recordId: 42,
        recordIndexPath: [0, 1],
      })
    ).toEqual({ record_id: 42, index_path: [0, 1] })
  })

  test('current record provider applies target element data scopes', () => {
    const dataProvider = testApp
      .getRegistry()
      .get('builderDataProvider', 'current_record')
    const table = {
      id: 2,
      type: 'table',
      page_id: 1,
      data_source_id: 1,
      schema_property: 'rows',
    }
    const page = {
      id: 1,
      dataSources: [
        {
          id: 1,
          type: 'csv_file_reader',
          schema: {
            type: 'array',
            items: {
              properties: {
                rows: {
                  type: 'array',
                  items: { properties: { name: { type: 'string' } } },
                },
              },
            },
          },
        },
      ],
      elementMap: { 2: table },
      orderedElements: [table],
      graph: { 0: 2, 2: {} },
    }
    const applicationContext = {
      builder: { id: 1, pages: [page, { id: 2, shared: true }] },
      page,
      element: table,
    }

    expect(dataProvider.getDataSchema(applicationContext)).toBeNull()
    expect(
      dataProvider.getDataSchema({
        ...applicationContext,
        dataScope: DATA_SCOPES.INCLUDE_TARGET_ELEMENT,
      }).properties
    ).toHaveProperty('name')
    expect(
      dataProvider.getDataSchema({
        ...applicationContext,
        dataScope: DATA_SCOPES.INCLUDE_TARGET_DATA_SOURCE,
      }).properties
    ).toHaveProperty('rows')
  })

  test('table fields inside a repeat read their row while visibility reads the parent row', () => {
    const currentRecord = testApp
      .getRegistry()
      .get('builderDataProvider', 'current_record')
    const repeat = {
      id: 10,
      type: 'repeat',
      page_id: 1,
      data_source_id: 1,
      schema_property: null,
      _: {
        content: [
          { parentName: 'First', rows: [{ cellName: 'First cell' }] },
          { parentName: 'Second', rows: [{ cellName: 'Second cell' }] },
        ],
      },
    }
    const table = {
      id: 11,
      type: 'table',
      page_id: 1,
      data_source_id: null,
      schema_property: 'rows',
    }
    const heading = { id: 12, type: 'heading', page_id: 1 }
    const page = {
      id: 1,
      dataSources: [
        {
          id: 1,
          type: 'csv_file_reader',
          schema: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                parentName: { type: 'string' },
                rows: {
                  type: 'array',
                  items: {
                    type: 'object',
                    properties: { cellName: { type: 'string' } },
                  },
                },
              },
            },
          },
        },
      ],
      elementMap: { 10: repeat, 11: table, 12: heading },
      graph: {
        0: 10,
        10: { children: { '': [11] } },
        11: { next: { '': [12] } },
        12: {},
      },
    }
    const builder = { id: 1, pages: [page, { id: 2, shared: true }] }
    const parentContext = {
      builder,
      page,
      element: repeat,
      recordIndexPath: [1],
      dataScope: DATA_SCOPES.INCLUDE_TARGET_ELEMENT,
    }
    const tableContext = { ...parentContext, element: table }

    // A normal element inside the repeat reads the selected repeat record.
    expect(
      currentRecord.getDataChunk({ ...parentContext, element: heading }, [
        'parentName',
      ])
    ).toBe('Second')
    // The table's collection field reads its own selected row.
    expect(
      TableElement.methods.resolveRowFormula.call(
        {
          $registry: testApp.getRegistry(),
          applicationContext: tableContext,
          resolveFormula: (_formula, context) =>
            context['current_record.cellName'],
        },
        'get(current_record.cellName)',
        0
      )
    ).toBe('Second cell')
    expect(currentRecord.getDataSchema(tableContext).properties).toHaveProperty(
      'cellName'
    )

    // The table's visibility formula uses its parent repeat record instead.
    const visibilityContext = {
      ...tableContext,
      dataScope: DATA_SCOPES.EXCLUDE_TARGET_SUBTREE,
    }
    expect(currentRecord.getDataChunk(visibilityContext, ['parentName'])).toBe(
      'Second'
    )
    expect(
      currentRecord.getDataChunk(visibilityContext, ['cellName'])
    ).toBeNull()
    expect(
      currentRecord.getDataSchema(visibilityContext).properties
    ).not.toHaveProperty('cellName')

    // The nested collection's schema picker sees the parent row's `rows`
    // property, not the table row properties defined by that property.
    const dataSourceContext = {
      ...tableContext,
      dataScope: DATA_SCOPES.INCLUDE_TARGET_DATA_SOURCE,
    }
    expect(
      currentRecord.getDataSchema(dataSourceContext).properties
    ).toHaveProperty('rows')
    expect(
      currentRecord.getDataSchema(dataSourceContext).properties
    ).not.toHaveProperty('cellName')
  })

  test('record selector inside a repeat uses its own options but its parent for visibility', () => {
    const currentRecord = testApp
      .getRegistry()
      .get('builderDataProvider', 'current_record')
    const repeat = {
      id: 10,
      type: 'repeat',
      page_id: 1,
      data_source_id: 1,
      schema_property: null,
      _: {
        content: [{ parentName: 'First' }, { parentName: 'Second' }],
      },
    }
    const recordSelector = {
      id: 20,
      type: 'record_selector',
      page_id: 1,
      data_source_id: 2,
      schema_property: null,
      _: {
        content: [
          { id: 201, choiceName: 'First choice' },
          { id: 202, choiceName: 'Second choice' },
        ],
      },
    }
    const page = {
      id: 1,
      dataSources: [
        {
          id: 1,
          type: 'csv_file_reader',
          schema: {
            type: 'array',
            items: {
              type: 'object',
              properties: { parentName: { type: 'string' } },
            },
          },
        },
        {
          id: 2,
          type: 'csv_file_reader',
          schema: {
            type: 'array',
            items: {
              type: 'object',
              properties: { choiceName: { type: 'string' } },
            },
          },
        },
      ],
      elementMap: { 10: repeat, 20: recordSelector },
      graph: { 0: 10, 10: { children: { '': [20] } }, 20: {} },
    }
    const applicationContext = {
      builder: { id: 1, pages: [page, { id: 2, shared: true }] },
      page,
      element: recordSelector,
      recordIndexPath: [1],
      dataScope: DATA_SCOPES.INCLUDE_TARGET_ELEMENT,
    }

    const options = RecordSelectorElement.computed.resolvedOptions.call({
      $registry: testApp.getRegistry(),
      applicationContext,
      element: { option_name_suffix: { formula: '' } },
      elementContent: recordSelector._.content,
      getId: (record) => record.id,
      resolveFormula: (_formula, context) =>
        context['current_record.choiceName'],
      dataSourceType: { getRecordName: () => 'Option' },
      dataSource: page.dataSources[0],
      defaultValueOptions: [],
      fallbackOptions: [],
      $t: (key) => key,
    })
    expect(options.map(({ nameSuffix }) => nameSuffix)).toEqual([
      'First choice',
      'Second choice',
    ])
    expect(
      currentRecord.getDataSchema(applicationContext).properties
    ).toHaveProperty('choiceName')
    expect(
      currentRecord.getDataSchema({
        ...applicationContext,
        dataScope: DATA_SCOPES.EXCLUDE_TARGET_SUBTREE,
      }).properties
    ).toHaveProperty('parentName')
    expect(
      currentRecord.getDataChunk(
        {
          ...applicationContext,
          dataScope: DATA_SCOPES.EXCLUDE_TARGET_SUBTREE,
        },
        ['parentName']
      )
    ).toBe('Second')
    expect(
      currentRecord.getDataChunk(
        {
          ...applicationContext,
          dataScope: DATA_SCOPES.EXCLUDE_TARGET_SUBTREE,
        },
        ['choiceName']
      )
    ).toBeNull()
  })
})
