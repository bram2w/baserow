import { vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { matchedRouteKey } from 'vue-router'
import { TestApp } from '@baserow/test/helpers/testApp'
import { clone } from '@baserow/modules/core/utils/object'
import AgentApplicationContent from '@baserow/modules/agent/components/AgentApplicationContent'

export const workspace = {
  id: 1,
  name: 'Workspace',
  generative_ai_models_enabled: { openai: ['model-one', 'model-two'] },
  ai_features: { ai_agent: { models: { openai: ['model-one', 'model-two'] } } },
}

export const agentData = {
  id: 10,
  name: 'Support agent',
  type: 'agent',
  readiness: 'ready',
  workspace: { id: 1 },
}

export const completeConfiguration = (extra = {}) => ({
  instructions: 'Be helpful.',
  provider_type: 'openai',
  model_identifier: 'model-one',
  readiness: 'ready',
  errors: {},
  ...extra,
})

export const incompleteConfiguration = (field) =>
  completeConfiguration({
    [field]: field === 'instructions' ? '' : null,
    readiness: 'incomplete',
    errors: { [field]: 'required' },
  })

export const unavailableModel = (model) =>
  completeConfiguration({
    model_identifier: model,
    readiness: 'unavailable',
    errors: { model_identifier: 'unavailable' },
  })

export const deferredReply = () => {
  let resolve
  return {
    reply: () =>
      new Promise((r) => {
        resolve = r
      }),
    resolve: (status, data) => resolve([status, data]),
  }
}

export const withoutConfiguration = (operation) =>
  !['agent_application.read_configuration', 'application.update'].includes(
    operation
  )

// One handler per route, because axios-mock-adapter matches an earlier reply first.
function respond(handler, ...responses) {
  const queue = [...responses]
  handler.reply((config) => {
    const response = queue.length > 1 ? queue.shift() : queue[0]
    if (typeof response === 'function') return response(config)
    const isTuple = Array.isArray(response) && typeof response[0] === 'number'
    return isTuple ? response : [200, response]
  })
}

export const mockAgent = (testApp, ...responses) =>
  respond(testApp.mock.onGet('/applications/10/'), ...responses)

export const mockRename = (testApp, ...responses) =>
  respond(testApp.mock.onPatch('/applications/10/'), ...responses)

export const mockConfiguration = (testApp, ...responses) =>
  respond(testApp.mock.onGet('/agent/10/configuration/'), ...responses)

export const mockSaves = (testApp, ...responses) =>
  respond(testApp.mock.onPatch('/agent/10/configuration/'), ...responses)

export const mockAvailability = (testApp, ...responses) =>
  respond(testApp.mock.onGet('/workspaces/'), ...responses)

export const savedValues = (testApp) =>
  testApp.mock.history.patch
    .filter(({ url }) => url === '/agent/10/configuration/')
    .map(({ data }) => JSON.parse(data))

export async function createAgentPage() {
  const testApp = new TestApp()
  const allowed = ref(() => true)
  await testApp.store.dispatch('workspace/forceCreate', clone(workspace))
  const agent = await testApp.store.dispatch(
    'application/forceCreate',
    clone(agentData)
  )
  mockAvailability(testApp, [workspace])
  mockAgent(testApp, agentData)
  mockConfiguration(testApp, completeConfiguration())
  // Nuxt's $hasPermission is a non-configurable getter, so override a child.
  const permissionApp = Object.create(testApp.nuxtApp)
  Object.defineProperty(permissionApp, '$hasPermission', {
    value: (operation) => allowed.value(operation),
  })
  const route = { leaveGuards: new Set(), updateGuards: new Set() }
  return {
    testApp,
    agent,
    allowed,
    mount: () =>
      testApp.mount(AgentApplicationContent, {
        props: { agent },
        global: {
          provide: { [matchedRouteKey]: ref(route) },
          plugins: [{ install: (app) => (app.$nuxt = permissionApp) }],
        },
      }),
    leave: () => [...route.leaveGuards][0](),
    update: (to, from) => [...route.updateGuards][0](to, from),
  }
}

export async function destroyAgentPage(testApp) {
  await testApp.afterEach()
  vi.restoreAllMocks()
  vi.clearAllTimers()
  vi.useRealTimers()
}

export const useFakeTimers = () =>
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'Date'] })

export const warning = (wrapper) => wrapper.find('.agent-chat__warning')

export const saving = (wrapper) =>
  wrapper.find('.agent-configuration__header [role="status"]')

export const openSection = (wrapper, key) =>
  wrapper
    .findAll('.agent-configuration__section')
    .find((button) => button.text().includes(key))
    .trigger('click')

export const instructions = (wrapper) =>
  wrapper.get('.agent-configuration textarea')

export async function editInstructions(wrapper, value) {
  await instructions(wrapper).setValue(value)
  await instructions(wrapper).trigger('blur')
  await flushPromises()
}

const field = (wrapper, label) =>
  wrapper
    .findAll('.agent-configuration__body .control')
    .find((control) => control.get('.control__label').text().includes(label))

export const nameInput = (wrapper) => field(wrapper, 'agent.name').get('input')

export const providerDropdown = (wrapper) =>
  field(wrapper, 'agent.provider').get('.dropdown')

export const modelDropdown = (wrapper) =>
  field(wrapper, 'agent.model').get('.dropdown')

export const modelError = (wrapper) =>
  field(wrapper, 'agent.model').find('.control__messages--error')

export async function choose(dropdown, text) {
  await dropdown.get('.dropdown__selected').trigger('click')
  await dropdown
    .findAll('.select__item-link')
    .find((item) => item.text().includes(text))
    .trigger('click')
}
