import { expect } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import MockAdapter from 'axios-mock-adapter'

import { registerRealtimeEvents } from '@baserow_enterprise/realtime'
import AgentFollowUpsSection from '@baserow_enterprise/components/agentApplication/AgentFollowUpsSection'
import {
  describeWatch,
  followUpFields,
} from '@baserow_enterprise/utils/agentFollowUp'
import { approvalActsAsUser } from '@baserow_enterprise/utils/agentToolIdentities'

const ME = 7
const application = { id: 42, workspace: { id: 1 } }

const followUp = (id, values = {}) => ({
  id,
  application_id: 42,
  title: `Follow-up ${id}`,
  goal: 'Know when it closes.',
  check_instructions: 'Read row 1.',
  done_when: 'Closed.',
  watch: { type: 'schedule', every: 'hour' },
  state: 'Open.',
  status: 'active',
  outcome: '',
  private: false,
  created_by: { id: ME, name: 'Ann' },
  source_chat_uuid: 'chat-1',
  created_on: '2026-10-14T10:00:00Z',
  expires_on: '2026-11-13T10:00:00Z',
  last_checked_on: null,
  checks_count: 0,
  notifications_count: 0,
  total_input_tokens: 0,
  total_output_tokens: 0,
  total_cost: '0',
  unpriced_turns: 0,
  ...values,
})

// Translations aren't loaded in unit tests; the key and its values show what
// would be rendered.
const t = (key, values) => (values ? `${key} ${JSON.stringify(values)}` : key)

describe('follow-ups', () => {
  let store = null
  let mock = null
  let events = null

  beforeEach(async () => {
    const { $store, $client } = useNuxtApp()
    store = $store
    mock = new MockAdapter($client, { onNoMatch: 'throwException' })
    store.state.auth.user = { id: ME }
    events = {}
    registerRealtimeEvents({
      registerEvent(name, handler) {
        events[name] = handler
      },
    })
    await store.dispatch('agentApplication/forceUpdate', {
      values: { id: 3, application_id: 42, name: 'Agent' },
    })
    store.commit('agentApplication/SET_FOLLOW_UPS', [])
    if (!store.getters['application/get'](42)) {
      await store.dispatch('application/forceCreate', {
        id: 42,
        type: 'agent',
        name: 'Agent',
        order: 1,
        workspace: { id: 1 },
      })
    }
  })

  afterEach(() => {
    mock.restore()
  })

  test('the watch and details are described for people', () => {
    expect(describeWatch({ type: 'schedule', every: 'hour' }, t)).toBe(
      'agentFollowUps.every_hour'
    )
    expect(
      describeWatch(
        { type: 'rows_updated', table_name: 'Issues', row_ids: [1, 2] },
        t
      )
    ).toBe(
      'agentFollowUps.watch_rows_updated {"table":"Issues","rows":"1, 2","count":2}'
    )
    const fields = followUpFields(
      followUp(1, {
        state: '',
        watch: { type: 'rows_created', table_name: 'Issues', row_ids: [] },
      }),
      t
    )
    expect(fields.map((field) => field.key)).toEqual([
      'agentFollowUps.goal',
      'agentFollowUps.when',
      'agentFollowUps.table',
      'agentFollowUps.check',
      'agentFollowUps.doneWhen',
      'agentFollowUps.notifies',
      'agentFollowUps.until',
    ])
    expect(fields.find((field) => field.kind === 'member').value).toBe('Ann')
  })

  test('only the conversations user decides on a follow-up', () => {
    const context = { tools: [], catalog: [], application: {} }
    expect(approvalActsAsUser('propose_follow_up', context)).toBe(true)
    expect(approvalActsAsUser('something_else', context)).toBe(false)
  })

  test('realtime updates keep the list current for whom it concerns', async () => {
    const app = { $hasPermission: () => false }
    await events.agent_follow_up_updated(
      { store, app },
      { follow_up: followUp(1) }
    )
    // Someone else's, and this user doesn't manage follow-ups.
    await events.agent_follow_up_updated(
      { store, app },
      { follow_up: followUp(2, { created_by: { id: 99, name: 'Bo' } }) }
    )
    // The redacted copy of the user's own private follow-up; the full one
    // arrives separately.
    await events.agent_follow_up_updated(
      { store, app },
      {
        follow_up: followUp(1, { title: '', status: 'completed' }),
        except_user_id: ME,
      }
    )
    // Another agent's.
    await events.agent_follow_up_updated(
      { store, app },
      { follow_up: followUp(3, { application_id: 99 }) }
    )

    expect(
      store.getters['agentApplication/getFollowUps'].map((item) => [
        item.id,
        item.title,
      ])
    ).toEqual([[1, 'Follow-up 1']])

    await events.agent_follow_up_updated(
      { store, app: { $hasPermission: () => true } },
      { follow_up: followUp(2, { created_by: { id: 99, name: 'Bo' } }) }
    )
    expect(store.getters['agentApplication/getFollowUps']).toHaveLength(2)
  })

  test('the section lists active follow-ups and stops one', async () => {
    store.commit('agentApplication/SET_FOLLOW_UPS', [
      followUp(1),
      followUp(2, { status: 'completed', outcome: 'It was closed.' }),
      followUp(3, {
        private: true,
        title: '',
        created_by: { id: 99, name: 'Bo' },
      }),
    ])
    const wrapper = await mountSuspended(AgentFollowUpsSection, {
      props: { application },
    })

    const titles = () =>
      wrapper
        .findAll('.agent-configuration__card-name')
        .map((name) => name.text())
    expect(titles()).toEqual(['Follow-up 1', 'agentFollowUps.privateTitle'])

    await wrapper.findAll('.segment-control__button').at(1).trigger('click')
    expect(titles()).toEqual(['Follow-up 2'])

    await wrapper.findAll('.segment-control__button').at(0).trigger('click')
    mock
      .onPost('agent_application/follow_ups/1/check/')
      .replyOnce(200, { id: 50, uuid: 'check-1' })
    await wrapper
      .findAll('button')
      .find((button) => button.text().includes('agentFollowUps.checkNow'))
      .trigger('click')
    await flushPromises()
    // The check opens so the result is visible, also when nothing changed.
    expect(wrapper.emitted('open-conversation')).toEqual([['check-1']])

    mock
      .onDelete('agent_application/follow_ups/1/')
      .replyOnce(200, followUp(1, { status: 'cancelled' }))
    // The test user may manage follow-ups, so the private one can be stopped
    // as well; the user's own comes first.
    const stop = wrapper
      .findAll('button')
      .filter((button) => button.text().includes('agentFollowUps.cancel'))
    expect(stop).toHaveLength(2)
    await stop[0].trigger('click')
    await flushPromises()

    expect(titles()).toEqual(['agentFollowUps.privateTitle'])
  })
})
