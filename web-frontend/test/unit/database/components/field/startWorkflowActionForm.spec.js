import { readFileSync } from 'fs'
import { resolve } from 'path'
import { TestApp } from '@baserow/test/helpers/testApp'
import DatabaseWorkflowActionWithService from '@baserow/modules/database/components/field/DatabaseWorkflowActionWithService'

// The i18n loader compiles imported locale files into message ASTs.
const en = JSON.parse(
  readFileSync(
    resolve(process.cwd(), 'modules/integrations/locales/en.json'),
    'utf8'
  )
)
const enDatabase = JSON.parse(
  readFileSync(
    resolve(process.cwd(), 'modules/database/locales/en.json'),
    'utf8'
  )
)

const WORKSPACE_ID = 1
const DATABASE_ID = 100
const AUTOMATION_ID = 200

describe('start workflow action form', () => {
  let testApp = null

  beforeEach(async () => {
    testApp = new TestApp()
    const workspace = { id: WORKSPACE_ID, name: 'Acme', users: [] }
    await testApp.store.dispatch('workspace/forceCreate', workspace)
    // `workspace/select` would fetch permissions and roles.
    testApp.store.commit(
      'workspace/SET_SELECTED',
      testApp.store.getters['workspace/get'](WORKSPACE_ID)
    )
    await testApp.store.dispatch('application/forceCreate', {
      id: DATABASE_ID,
      name: 'Customers',
      type: 'database',
      workspace: { id: WORKSPACE_ID },
      tables: [],
    })
    await testApp.store.dispatch('application/forceCreate', {
      id: AUTOMATION_ID,
      name: 'Onboarding',
      type: 'automation',
      order: 1,
      workspace: { id: WORKSPACE_ID },
      workflows: [
        { id: 11, name: 'Send welcome', order: 1, immediate_dispatch: true },
        { id: 12, name: 'Nightly sync', order: 2, immediate_dispatch: false },
      ],
    })
  })

  afterEach(() => testApp.afterEach())

  const database = () => testApp.store.getters['application/get'](DATABASE_ID)

  test('only a workflow that can be started immediately is offered', async () => {
    const wrapper = await testApp.mount(DatabaseWorkflowActionWithService, {
      props: {
        workflowAction: { id: 1, type: 'start_workflow', service: {} },
        database: database(),
        defaultValues: { service: {} },
      },
    })

    await wrapper.findComponent({ name: 'Dropdown' }).vm.show()
    await wrapper.vm.$nextTick()

    const names = wrapper
      .findAll('.select__item-link')
      .map((item) => item.text())
    expect(names).toContain('Send welcome')
    expect(names).not.toContain('Nightly sync')
  })

  test('picking a workflow reaches the action', async () => {
    const wrapper = await testApp.mount(DatabaseWorkflowActionWithService, {
      props: {
        workflowAction: { id: 1, type: 'start_workflow', service: {} },
        database: database(),
        defaultValues: { service: {} },
      },
    })

    await wrapper.findComponent({ name: 'Dropdown' }).vm.show()
    await wrapper.vm.$nextTick()
    await wrapper.find('.select__item-link').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.values.service.workflow_id).toBe(11)
  })

  test('an action with no workflow yet says so', () => {
    const type = testApp._app.$registry.get(
      'databaseWorkflowActionType',
      'start_workflow'
    )

    const message = type.getErrorMessage(
      { id: 1, type: 'start_workflow', service: { workflow_id: null } },
      { database: database() }
    )

    expect(message).toBeTruthy()
  })

  test('a workflow that cannot start immediately says so', () => {
    const type = testApp._app.$registry.get(
      'databaseWorkflowActionType',
      'start_workflow'
    )

    const message = type.getErrorMessage(
      { id: 1, type: 'start_workflow', service: { workflow_id: 12 } },
      { database: database() }
    )

    // `$t` returns the key here.
    expect(message).toBe('serviceType.errorWorkflowNotImmediateDispatch')
    expect(en.serviceType.errorWorkflowNotImmediateDispatch).toBe(
      'The selected workflow must use a trigger that can start immediately.'
    )
  })

  const startWorkflowType = () =>
    testApp._app.$registry.get('databaseWorkflowActionType', 'start_workflow')

  const missingWorkflowAction = {
    id: 1,
    type: 'start_workflow',
    service: { workflow_id: 999 },
  }

  test('a workflow the loaded applications do not hold is called out', async () => {
    await testApp.store.dispatch('application/forceSetAll', {
      applications: [
        {
          id: DATABASE_ID,
          name: 'Customers',
          type: 'database',
          workspace: { id: WORKSPACE_ID },
          tables: [],
        },
        {
          id: AUTOMATION_ID,
          name: 'Onboarding',
          type: 'automation',
          order: 1,
          workspace: { id: WORKSPACE_ID },
          workflows: [
            {
              id: 11,
              name: 'Send welcome',
              order: 1,
              immediate_dispatch: true,
            },
          ],
        },
      ],
    })

    const message = startWorkflowType().getErrorMessage(missingWorkflowAction, {
      database: database(),
      workspace: { id: WORKSPACE_ID },
    })

    // `$t` returns the key here. The copy must not claim the workflow was
    // deleted: applications are filtered by what the reader may see.
    expect(message).toBe('databaseWorkflowActionType.startWorkflowMissing')
    expect(enDatabase.databaseWorkflowActionType.startWorkflowMissing).toBe(
      "This action's workflow can't be found. It may have been deleted, or " +
        'you may not have access to it. Pick another workflow, or ask ' +
        'someone who can see this one.'
    )
  })

  test('nothing is said while the applications are still being fetched', () => {
    // `forceCreate` never marks the list fetched.
    expect(testApp.store.getters['application/isLoaded']).toBe(false)

    const message = startWorkflowType().getErrorMessage(missingWorkflowAction, {
      database: database(),
      workspace: { id: WORKSPACE_ID },
    })

    expect(message).toBeNull()
  })
})
