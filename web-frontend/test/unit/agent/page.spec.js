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
      workspace: { id: 1 },
    })
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('loads the agent once so the visit is recorded', async () => {
    testApp.mock.onGet('/agent/10/').reply(200, {})

    await testApp.mount(AgentPage, {
      global: { provide: { [PageRouteSymbol]: { params: { agentId: '10' } } } },
    })
    await flushPromises()

    expect(
      testApp.mock.history.get.filter(({ url }) => url === '/agent/10/')
    ).toHaveLength(1)
  })
})
