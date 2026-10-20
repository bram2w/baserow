import { afterEach, beforeEach, describe, expect, test } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import {
  createAgentPage,
  deferredReply,
  destroyAgentPage,
  mockAvailability,
  warning,
  withoutSettings,
} from './helpers'

describe('Agent model availability', () => {
  let testApp, agent, allowed, mount

  beforeEach(async () => {
    ;({ testApp, agent, allowed, mount } = await createAgentPage())
  })

  afterEach(() => destroyAgentPage(testApp))

  const modelRequests = () =>
    testApp.mock.history.get.filter(({ url }) => url === '/workspaces/')

  test('uses public readiness without loading models for ordinary readers', async () => {
    allowed.value = withoutSettings
    mockAvailability(testApp, [500, {}])

    const wrapper = await mount()

    expect(modelRequests()).toHaveLength(0)
    expect(warning(wrapper).exists()).toBe(false)
  })

  test('does not load models for a public realtime update to an ordinary reader', async () => {
    allowed.value = withoutSettings
    const wrapper = await mount()

    await testApp.store.dispatch('application/forceUpdate', {
      application: agent,
      data: { name: 'Updated agent', readiness: 'ready' },
    })
    await flushPromises()

    expect(modelRequests()).toHaveLength(0)
    expect(warning(wrapper).exists()).toBe(false)
  })

  test('loads models when settings access is granted', async () => {
    allowed.value = withoutSettings
    const wrapper = await mount()
    expect(modelRequests()).toHaveLength(0)

    allowed.value = () => true
    await flushPromises()

    expect(modelRequests()).toHaveLength(1)
    expect(wrapper.find('.agent-configuration').exists()).toBe(true)
    expect(warning(wrapper).exists()).toBe(false)
  })

  test('ignores a pending model failure after settings access is revoked', async () => {
    testApp.dontFailOnErrorResponses()
    const models = deferredReply()
    mockAvailability(testApp, models.reply)
    const wrapper = await mount()

    allowed.value = withoutSettings
    await flushPromises()
    models.resolve(500, {})
    await flushPromises()

    expect(wrapper.find('.agent-configuration').exists()).toBe(false)
    expect(warning(wrapper).exists()).toBe(false)
  })
})
