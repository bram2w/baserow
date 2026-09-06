import { TestApp } from '@baserow/test/helpers/testApp'
import DatabaseWorkflowActionWithService from '@baserow/modules/database/components/field/DatabaseWorkflowActionWithService'

const WORKSPACE_ID = 1
const DATABASE_ID = 100
const AUTOMATION_ID = 200

describe('start workflow action form', () => {
  let testApp = null

  beforeEach(async () => {
    testApp = new TestApp()
    const workspace = { id: WORKSPACE_ID, name: 'Acme', users: [] }
    await testApp.store.dispatch('workspace/forceCreate', workspace)
    // Committed rather than dispatched: `workspace/select` fetches
    // permissions and roles, which this form does not need.
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
})
