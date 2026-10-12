import {
  chatMatchesOrigin,
  describeChatOrigin,
  getChatOrigin,
} from '@baserow_enterprise/utils/agentChatOrigin'

describe('agentChatOrigin', () => {
  test('derives the origin of a conversation', () => {
    expect(getChatOrigin({ source: 'manual' })).toBe('manual')
    expect(getChatOrigin({ source: 'setup' })).toBe('manual')
    expect(getChatOrigin({ source: 'service' })).toBe('service')
    expect(
      getChatOrigin({ source: 'trigger', trigger_type: 'rows_created' })
    ).toBe('trigger:rows_created')
    expect(getChatOrigin({ source: 'channel', channel_type: 'slack' })).toBe(
      'channel:slack'
    )
  })

  test('describes origins with registered types and falls back otherwise', () => {
    const types = {
      'node:local_baserow_rows_created': {
        name: 'Rows are created',
        iconClass: 'iconoir-table',
      },
      'agentChatChannel:slack': { name: 'Slack', icon: '', image: 'slack.svg' },
    }
    const registry = {
      get(namespace, type) {
        const found = types[`${namespace}:${type}`]
        if (!found) {
          throw new Error('not found')
        }
        return found
      },
    }
    const t = (key) => key

    expect(
      describeChatOrigin('trigger:rows_created', { registry, t })
    ).toMatchObject({ label: 'Rows are created', icon: 'iconoir-table' })
    expect(describeChatOrigin('channel:slack', { registry, t })).toMatchObject({
      label: 'Slack',
      image: 'slack.svg',
    })
    expect(describeChatOrigin('channel:gone', { registry, t }).label).toBe(
      'agentChatOrigin.channel'
    )
    expect(describeChatOrigin('manual', { registry, t }).label).toBe(
      'agentChatOrigin.manual'
    )
  })

  test('matches conversations against a filter, including created by me', () => {
    const own = { source: 'manual', user_id: 1 }
    const triggered = {
      source: 'trigger',
      trigger_type: 'periodic',
      user_id: null,
    }
    expect(chatMatchesOrigin(triggered, null, 1)).toBe(true)
    expect(chatMatchesOrigin(own, 'mine', 1)).toBe(true)
    expect(chatMatchesOrigin(own, 'mine', 2)).toBe(false)
    expect(chatMatchesOrigin(triggered, 'mine', 1)).toBe(false)
    expect(chatMatchesOrigin(triggered, 'trigger:periodic', 1)).toBe(true)
  })
})
