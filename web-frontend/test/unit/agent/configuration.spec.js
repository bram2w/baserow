import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import {
  agentData,
  choose,
  completeConfiguration,
  createAgentPage,
  deferredReply,
  destroyAgentPage,
  editInstructions,
  incompleteConfiguration,
  instructions,
  mockAgent,
  mockAvailability,
  mockConfiguration,
  mockRename,
  mockSaves,
  modelDropdown,
  modelError,
  nameInput,
  openSection,
  providerDropdown,
  savedValues,
  saving,
  unavailableModel,
  useFakeTimers,
  warning,
  withoutConfiguration,
  workspace,
} from './helpers'

describe('Agent configuration', () => {
  let testApp, agent, allowed, mount, leave, update

  beforeEach(async () => {
    ;({ testApp, agent, allowed, mount, leave, update } =
      await createAgentPage())
  })

  afterEach(() => destroyAgentPage(testApp))

  test('toggles the configuration from the header', async () => {
    const wrapper = await mount()
    const toggle = wrapper.get('button[aria-label="agent.configuration"]')
    expect(wrapper.get('.agent-application__header-name').text()).toBe(
      'Support agent'
    )

    await toggle.trigger('click')
    expect(wrapper.find('.agent-configuration').exists()).toBe(false)
    expect(toggle.attributes('aria-expanded')).toBe('false')
    await toggle.trigger('click')

    expect(wrapper.find('.agent-configuration').exists()).toBe(true)
  })

  test('keeps the open form when the Agent changes in the background', async () => {
    const wrapper = await mount()
    await openSection(wrapper, 'agent.instructions')
    const textarea = instructions(wrapper).element
    const requests = testApp.mock.history.get.length

    await testApp.store.dispatch('application/forceUpdate', {
      application: agent,
      data: { last_viewed: '2026-10-20T10:00:00Z' },
    })
    await flushPromises()

    expect(instructions(wrapper).element).toBe(textarea)
    expect(testApp.mock.history.get).toHaveLength(requests)
  })

  test('keeps an unsaved edit when the session token is refreshed', async () => {
    const user = { id: 1, username: 'member@example.com' }
    testApp.authenticate(user)
    const wrapper = await mount()
    await openSection(wrapper, 'agent.instructions')
    await instructions(wrapper).setValue('Unsaved instructions')

    testApp.authenticate({ ...user })
    await flushPromises()

    expect(instructions(wrapper).element.value).toBe('Unsaved instructions')
  })

  test('saves typed text on blur and shows only the header spinner while saving', async () => {
    useFakeTimers()
    const patch = deferredReply()
    mockSaves(testApp, patch.reply)
    const wrapper = await mount()
    await openSection(wrapper, 'agent.instructions')
    await instructions(wrapper).setValue('Updated instructions')
    await vi.advanceTimersByTimeAsync(1000)
    expect(savedValues(testApp)).toEqual([])

    await instructions(wrapper).trigger('blur')
    await flushPromises()
    expect(saving(wrapper).attributes('aria-label')).toBe('agent.saving')
    expect(wrapper.find('.agent-configuration textarea').exists()).toBe(true)
    patch.resolve(
      200,
      completeConfiguration({ instructions: 'Updated instructions' })
    )
    await flushPromises()

    expect(saving(wrapper).exists()).toBe(false)
    expect(warning(wrapper).exists()).toBe(false)
  })

  test('queues an edit made during a save, even back to the saved value', async () => {
    const first = deferredReply()
    mockSaves(testApp, first.reply, completeConfiguration())
    const wrapper = await mount()
    await openSection(wrapper, 'agent.instructions')
    await editInstructions(wrapper, 'Changed instructions')
    await editInstructions(wrapper, 'Be helpful.')

    first.resolve(
      200,
      completeConfiguration({ instructions: 'Changed instructions' })
    )
    await flushPromises()

    expect(savedValues(testApp)).toEqual([
      { instructions: 'Changed instructions' },
      { instructions: 'Be helpful.' },
    ])
    expect(instructions(wrapper).element.value).toBe('Be helpful.')
  })

  test('saves pending edits before leaving the Agent', async () => {
    const first = deferredReply()
    const second = deferredReply()
    mockSaves(testApp, first.reply, second.reply)
    const wrapper = await mount()
    await openSection(wrapper, 'agent.instructions')
    await editInstructions(wrapper, 'Changed instructions')
    await instructions(wrapper).setValue('Be helpful.')
    const completed = vi.fn()
    const leaving = leave().then((result) => completed(result) || result)

    first.resolve(
      200,
      completeConfiguration({ instructions: 'Changed instructions' })
    )
    await flushPromises()
    expect(completed).not.toHaveBeenCalled()
    second.resolve(200, completeConfiguration())

    expect(await leaving).toBe(true)
    expect(savedValues(testApp)).toHaveLength(2)
  })

  test('stays on the Agent with the draft when saving before leaving fails', async () => {
    testApp.dontFailOnErrorResponses()
    mockSaves(testApp, [500, {}])
    const wrapper = await mount()
    await openSection(wrapper, 'agent.instructions')
    await instructions(wrapper).setValue('Unsaved instructions')

    expect(await leave()).toBe(false)
    await flushPromises()

    expect(instructions(wrapper).element.value).toBe('Unsaved instructions')
    expect(wrapper.text()).toContain('agent.configurationSaveError')
  })

  test('keeps the current Agent selected when saving before switching Agents fails', async () => {
    testApp.dontFailOnErrorResponses()
    testApp.mock.onGet('/workspaces/1/permissions/').reply(200, [])
    mockSaves(testApp, [500, {}])
    const next = await testApp.store.dispatch('application/forceCreate', {
      ...agentData,
      id: 11,
    })
    const wrapper = await mount()
    await openSection(wrapper, 'agent.instructions')
    await instructions(wrapper).setValue('Unsaved instructions')
    await testApp.store.dispatch('application/select', next)

    const switched = await update(
      { params: { agentId: '11' } },
      { params: { agentId: '10' } }
    )

    expect(switched).toBe(false)
    expect(testApp.store.getters['application/getSelected'].id).toBe(10)
  })

  test('keeps a failed model save without a required error until retry succeeds', async () => {
    testApp.dontFailOnErrorResponses()
    mockConfiguration(testApp, incompleteConfiguration('model_identifier'))
    mockSaves(testApp, [500, {}], completeConfiguration())
    const wrapper = await mount()
    await openSection(wrapper, 'agent.agentSettings')
    await choose(modelDropdown(wrapper), 'model-one')
    await flushPromises()

    expect(modelError(wrapper).exists()).toBe(false)
    expect(wrapper.text()).toContain('agent.configurationSaveError')
    await wrapper
      .get('.agent-configuration__save-status button')
      .trigger('click')
    await flushPromises()

    expect(wrapper.find('.agent-configuration__save-status').exists()).toBe(
      false
    )
    expect(warning(wrapper).exists()).toBe(false)
  })

  test('clears the model when the provider changes and then requires a model', async () => {
    mockAvailability(testApp, [
      {
        ...workspace,
        ai_features: {
          ai_agent: {
            models: { openai: ['model-one'], anthropic: ['claude'] },
          },
        },
      },
    ])
    mockSaves(testApp, {
      ...incompleteConfiguration('model_identifier'),
      provider_type: 'anthropic',
    })
    const wrapper = await mount()
    await openSection(wrapper, 'agent.agentSettings')

    await choose(providerDropdown(wrapper), 'anthropic')
    await flushPromises()

    expect(savedValues(testApp)).toEqual([
      { provider_type: 'anthropic', model_identifier: null },
    ])
    expect(modelError(wrapper).text()).toBe('error.requiredField')
  })

  test('keeps the model when the selected provider is chosen again', async () => {
    mockSaves(testApp, completeConfiguration({ model_identifier: null }))
    const wrapper = await mount()
    await openSection(wrapper, 'agent.agentSettings')

    await choose(providerDropdown(wrapper), 'openai')
    await flushPromises()

    expect(savedValues(testApp)).toEqual([])
  })

  test('ties an unavailable model error to the selection it was returned for', async () => {
    mockConfiguration(testApp, unavailableModel('retired-model'))
    const patch = deferredReply()
    mockSaves(testApp, patch.reply)
    const wrapper = await mount()
    await openSection(wrapper, 'agent.agentSettings')
    const model = modelDropdown(wrapper)
    expect(model.get('.dropdown__selected-text').text()).toBe('retired-model')
    expect(modelError(wrapper).text()).toBe('agent.modelUnavailable')

    await choose(model, 'model-two')
    expect(modelError(wrapper).exists()).toBe(false)
    await flushPromises()
    patch.resolve(200, unavailableModel('model-two'))
    await flushPromises()

    expect(modelError(wrapper).text()).toBe('agent.modelUnavailable')
  })

  test('does not restore an older required error over a newer queued selection', async () => {
    const incomplete = incompleteConfiguration('model_identifier')
    mockConfiguration(testApp, incomplete)
    const first = deferredReply()
    mockSaves(
      testApp,
      first.reply,
      completeConfiguration({ model_identifier: 'model-two' })
    )
    const wrapper = await mount()
    await openSection(wrapper, 'agent.instructions')
    await editInstructions(wrapper, 'Updated instructions')
    await wrapper
      .get('.agent-configuration__header button[aria-label="action.back"]')
      .trigger('click')
    await openSection(wrapper, 'agent.agentSettings')
    await choose(modelDropdown(wrapper), 'model-two')
    expect(modelError(wrapper).exists()).toBe(false)

    first.resolve(200, { ...incomplete, instructions: 'Updated instructions' })
    await flushPromises()
    expect(modelError(wrapper).exists()).toBe(false)
    await flushPromises()

    expect(savedValues(testApp)[1]).toEqual({ model_identifier: 'model-two' })
    expect(modelError(wrapper).exists()).toBe(false)
  })

  test.each([
    ['instructions', 'agent.instructions', '.agent-configuration textarea'],
    ['model_identifier', 'agent.model', '.agent-configuration .dropdown'],
  ])(
    'opens the configuration on the invalid %s field from its warning',
    async (field, label, selector) => {
      mockConfiguration(testApp, incompleteConfiguration(field))
      const wrapper = await mount()
      await wrapper
        .get('.agent-configuration__header button[aria-label="action.close"]')
        .trigger('click')

      await wrapper
        .findAll('.agent-chat__warning-link')
        .find((button) => button.text() === label)
        .trigger('click')
      await flushPromises()

      const target = wrapper.findAll(selector).at(-1).element
      expect(target.contains(document.activeElement)).toBe(true)
    }
  )

  test('flags the section that holds a missing setting', async () => {
    mockConfiguration(testApp, incompleteConfiguration('model_identifier'))
    const wrapper = await mount()

    const [instructionsSection, settingsSection] = wrapper.findAll(
      '.agent-configuration__section'
    )

    expect(
      instructionsSection
        .find('.agent-configuration__section-caret--error')
        .exists()
    ).toBe(false)
    expect(
      settingsSection
        .get('.agent-configuration__section-caret--error')
        .attributes('aria-label')
    ).toBe('agent.fieldError')
  })

  test('renames the Agent through the application with the trimmed name', async () => {
    mockRename(testApp, { ...agentData, name: 'Support' })
    const wrapper = await mount()
    await openSection(wrapper, 'agent.agentSettings')

    await nameInput(wrapper).setValue('  Support  ')
    await nameInput(wrapper).trigger('blur')
    await flushPromises()

    expect(
      testApp.mock.history.patch.map(({ url, data }) => [url, JSON.parse(data)])
    ).toEqual([['/applications/10/', { name: 'Support' }]])
    expect(nameInput(wrapper).element.value).toBe('Support')
    expect(wrapper.get('.agent-application__header-name').text()).toBe(
      'Support'
    )
  })

  test('restores the saved name instead of saving a blank one', async () => {
    const wrapper = await mount()
    await openSection(wrapper, 'agent.agentSettings')

    await nameInput(wrapper).setValue(' ')
    await nameInput(wrapper).trigger('blur')
    await flushPromises()

    expect(nameInput(wrapper).element.value).toBe('Support agent')
    expect(testApp.mock.history.patch).toEqual([])
  })

  test.each([
    ['cannot read', withoutConfiguration],
    [
      'can read but not edit',
      (operation) => operation !== 'application.update',
    ],
  ])(
    'asks members who %s the configuration to contact an administrator',
    async (_, permission) => {
      allowed.value = permission
      agent.readiness = 'incomplete'
      mockConfiguration(testApp, incompleteConfiguration('instructions'))
      const wrapper = await mount()

      expect(wrapper.text()).toContain('agent.configurationPermissionRequired')
      expect(wrapper.find('.agent-chat__warning-link').exists()).toBe(false)
    }
  )

  test.each(['ready', 'incomplete', 'unavailable'])(
    'uses the serialized %s readiness without another application request',
    async (readiness) => {
      allowed.value = withoutConfiguration
      agent.readiness = readiness
      const wrapper = await mount()

      expect(warning(wrapper).exists()).toBe(readiness !== 'ready')
      expect(testApp.mock.history.get.map(({ url }) => url)).toEqual([])
    }
  )

  test('never shows the configuration after read access is revoked during a save', async () => {
    const patch = deferredReply()
    mockSaves(testApp, patch.reply)
    const wrapper = await mount()
    await openSection(wrapper, 'agent.instructions')
    await editInstructions(wrapper, 'PRIVATE')

    allowed.value = withoutConfiguration
    await flushPromises()
    mockAgent(testApp, { ...agentData, readiness: 'incomplete' })
    patch.resolve(200, completeConfiguration({ instructions: 'PRIVATE' }))
    await flushPromises()

    expect(wrapper.find('.agent-configuration').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('PRIVATE')
    expect(testApp.store.getters['application/get'](10)).not.toHaveProperty(
      'instructions'
    )
    expect(wrapper.text()).toContain('agent.configurationPermissionRequired')
  })

  test('refreshes readiness when model availability changes', async () => {
    allowed.value = withoutConfiguration
    const wrapper = await mount()
    mockAgent(testApp, { ...agentData, readiness: 'unavailable' })

    await testApp.store.dispatch('workspace/forceUpdateGenerativeAIModels', {
      workspaceId: 1,
      generativeAIModelsEnabled: {},
      aiFeatures: { ai_agent: { models: {} } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('agent.configurationPermissionRequired')
  })

  test('warns when refreshing the readiness fails and retries it', async () => {
    allowed.value = withoutConfiguration
    testApp.dontFailOnErrorResponses()
    const wrapper = await mount()
    mockAgent(testApp, [500, {}], agentData)

    await testApp.store.dispatch('workspace/forceUpdateGenerativeAIModels', {
      workspaceId: 1,
      generativeAIModelsEnabled: {},
      aiFeatures: { ai_agent: { models: {} } },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('agent.readinessLoadError')

    await wrapper.get('.agent-chat__warning button').trigger('click')
    await flushPromises()

    expect(warning(wrapper).exists()).toBe(false)
    expect(
      testApp.mock.history.get.some(({ url }) => url === '/agent/10/')
    ).toBe(false)
  })

  test('shows a failed configuration load in the sidebar until retry', async () => {
    testApp.dontFailOnErrorResponses()
    mockConfiguration(testApp, [500, {}], completeConfiguration())
    const wrapper = await mount()
    expect(wrapper.text()).toContain('agent.configurationLoadError')
    expect(wrapper.findAll('.agent-configuration__section')).toHaveLength(0)

    await wrapper
      .get('.agent-configuration__body .alert button')
      .trigger('click')
    await flushPromises()

    expect(wrapper.findAll('.agent-configuration__section')).toHaveLength(2)
  })

  test('warns when model availability cannot be loaded until retry', async () => {
    testApp.dontFailOnErrorResponses()
    mockAvailability(testApp, [500, {}], [workspace])
    const wrapper = await mount()
    expect(wrapper.text()).toContain('agent.readinessLoadError')

    await wrapper.get('.agent-chat__warning button').trigger('click')
    await flushPromises()

    expect(warning(wrapper).exists()).toBe(false)
  })
})
