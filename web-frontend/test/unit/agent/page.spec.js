import { afterEach, beforeEach, describe, expect, test } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { PageRouteSymbol } from '#app/components/injections'
import { TestApp } from '@baserow/test/helpers/testApp'
import AgentPage from '@baserow/modules/agent/pages/agent'

describe('Agent page', () => {
  let testApp

  beforeEach(async () => {
    testApp = new TestApp()
    await testApp.store.dispatch('application/forceCreate', {
      id: 10,
      name: 'Agent',
      type: 'agent',
      readiness: 'ready',
      workspace: { id: 1 },
    })
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('loads the agent once and uses its returned public data', async () => {
    testApp.mock.onGet('/agent/10/').reply(200, {
      id: 10,
      type: 'agent',
      name: 'Loaded agent',
      readiness: 'incomplete',
      workspace: { id: 1 },
    })

    const wrapper = await testApp.mount(AgentPage, {
      global: { provide: { [PageRouteSymbol]: { params: { agentId: '10' } } } },
    })
    await flushPromises()

    expect(
      testApp.mock.history.get.filter(({ url }) => url === '/agent/10/')
    ).toHaveLength(1)
    expect(wrapper.get('.agent-application__header-name').text()).toBe(
      'Loaded agent'
    )
    expect(testApp.store.getters['application/get'](10).readiness).toBe(
      'incomplete'
    )
    expect(
      testApp.mock.history.get.some(({ url }) => url.includes('/readiness/'))
    ).toBe(false)
    expect(
      testApp.mock.history.get.some(({ url }) => url === '/applications/10/')
    ).toBe(false)
  })
})
