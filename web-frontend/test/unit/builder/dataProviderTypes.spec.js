import { TestApp } from '@baserow/test/helpers/testApp'
import { DATA_SCOPES } from '@baserow/modules/builder/constants'

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
})
