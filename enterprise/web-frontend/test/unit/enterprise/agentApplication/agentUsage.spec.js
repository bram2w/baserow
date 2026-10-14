import { expect, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import MockAdapter from 'axios-mock-adapter'

import { registerRealtimeEvents } from '@baserow_enterprise/realtime'
import {
  formatCost,
  formatTokens,
  hasCost,
} from '@baserow_enterprise/utils/agentUsage'

const PERIOD = {
  input_tokens: 1000,
  output_tokens: 200,
  cost: 0.25,
  turns: 2,
  unpriced_turns: 0,
}
const USAGE = { today: PERIOD, week: PERIOD, month: PERIOD, lifetime: PERIOD }

describe('agent usage', () => {
  let store = null
  let mock = null
  let events = null

  beforeEach(async () => {
    const { $store, $client } = useNuxtApp()
    store = $store
    mock = new MockAdapter($client, { onNoMatch: 'throwException' })
    events = {}
    registerRealtimeEvents({
      registerEvent(name, handler) {
        events[name] = handler
      },
    })
    await store.dispatch('agentApplication/forceUpdate', {
      values: { id: 7, application_id: 42, name: 'Agent' },
    })
    store.dispatch('agentChat/newConversation')
  })

  afterEach(() => {
    mock.restore()
    vi.useRealTimers()
  })

  test('tokens and costs are formatted shortly', () => {
    expect(formatTokens(950)).toBe('950')
    expect(formatTokens(12345)).toBe('12k')
    expect(formatTokens(1250)).toBe('1.3k')
    expect(formatTokens(2000000)).toBe('2M')
    expect(formatCost(3.4)).toBe('$3.40')
    expect(formatCost(0.004)).toBe('<$0.01')
    expect(formatCost(0)).toBe('$0.00')
    expect(hasCost({ cost: 0 })).toBe(false)
    expect(hasCost({ total_cost: '0.0100000000' })).toBe(true)
  })

  test('the usage is fetched in the viewers timezone', async () => {
    mock
      .onGet('agent_application/42/usage/', {
        params: { timezone: Intl.DateTimeFormat().resolvedOptions().timeZone },
      })
      .replyOnce(200, USAGE)

    await store.dispatch('agentApplication/fetchUsage', { applicationId: 42 })

    expect(store.getters['agentApplication/getUsage']).toEqual({
      applicationId: 42,
      ...USAGE,
    })
  })

  test('usage changes are fetched at most once per interval', async () => {
    vi.useFakeTimers()
    mock.onGet('agent_application/42/usage/').reply(200, USAGE)
    await store.dispatch('agentApplication/fetchUsage', { applicationId: 42 })
    mock.resetHistory()

    // Another agent's usage is not this page's business.
    await events.agent_usage_updated({ store }, { application_id: 99 })
    for (let turn = 0; turn < 3; turn++) {
      await events.agent_usage_updated({ store }, { application_id: 42 })
    }
    expect(mock.history.get.length).toBe(0)

    await vi.advanceTimersByTimeAsync(2000)
    await flushPromises()
    expect(mock.history.get.length).toBe(1)

    // Once the interval has passed, a change is fetched right away.
    await vi.advanceTimersByTimeAsync(2000)
    await events.agent_usage_updated({ store }, { application_id: 42 })
    await vi.advanceTimersByTimeAsync(0)
    await flushPromises()
    expect(mock.history.get.length).toBe(2)
  })

  test('the open conversation keeps its totals up to date', async () => {
    mock.onGet('agent_application/42/chats/uuid-9/messages/').replyOnce(200, {
      chat: {
        id: 9,
        uuid: 'uuid-9',
        status: 'idle',
        total_input_tokens: 100,
        total_output_tokens: 20,
        total_cost: 0.01,
        unpriced_turns: 0,
      },
      messages: [],
    })
    await store.dispatch('agentChat/openConversation', {
      applicationId: 42,
      chatUuid: 'uuid-9',
    })
    expect(store.getters['agentChat/getUsage'].total_input_tokens).toBe(100)

    await store.dispatch('agentChat/handleChatUpdated', {
      chat: {
        id: 9,
        status: 'idle',
        total_input_tokens: 300,
        total_output_tokens: 40,
        total_cost: 0.03,
        unpriced_turns: 1,
      },
    })
    expect(store.getters['agentChat/getUsage']).toEqual({
      total_input_tokens: 300,
      total_output_tokens: 40,
      total_cost: 0.03,
      unpriced_turns: 1,
    })

    // A running turn counts up live before anything is persisted.
    await store.dispatch('agentChat/handleRealtimeEvent', {
      chatId: 9,
      event: {
        type: 'ai/usage',
        total_input_tokens: 900,
        total_output_tokens: 60,
        total_cost: '0.0500000000',
        unpriced_turns: 1,
      },
    })
    expect(store.getters['agentChat/getUsage'].total_input_tokens).toBe(900)
    expect(store.getters['agentChat/getUsage'].total_cost).toBe('0.0500000000')

    store.dispatch('agentChat/newConversation')
    expect(store.getters['agentChat/getUsage']).toBe(null)
  })
})
