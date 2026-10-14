import { mountSuspended } from '@nuxt/test-utils/runtime'

import AgentChatToolGroup from '@baserow_enterprise/components/agentApplication/AgentChatToolGroup'

const step = (id, result) => ({
  kind: 'tool',
  key: `tool-${id}`,
  event: {
    id,
    type: 'tool_call',
    tool_name: 'load_row_tools',
    args: { thought: 'Enable row creation', table_ids: [1] },
    result,
  },
})

async function mount(steps, hasError) {
  return await mountSuspended(AgentChatToolGroup, {
    props: {
      block: {
        type: 'tool_group',
        key: 'g',
        steps,
        toolCount: steps.length,
        live: false,
        hasError,
      },
      toolLabel: (name) => name,
      applications: [],
    },
  })
}

describe('AgentChatToolGroup', () => {
  test('a failed step shows its error inline', async () => {
    const wrapper = await mount(
      [
        step(1, { status: 'ok', content: { tables: [] } }),
        step(2, {
          status: 'error',
          content: { error: 'The tool load_row_tools failed: boom' },
        }),
      ],
      true
    )
    await wrapper.find('.agent-chat-tool-group__header').trigger('click')
    const errors = wrapper.findAll('.agent-chat-tool-group__step-error')
    expect(errors).toHaveLength(1)
    expect(errors[0].text()).toBe('The tool load_row_tools failed: boom')
    expect(
      wrapper.findAll('.agent-chat-tool-group__step-status--error')
    ).toHaveLength(1)
  })

  test('a search shows what it searches for, other steps their thought', async () => {
    const search = {
      kind: 'tool',
      key: 'tool-3',
      event: {
        id: 3,
        type: 'tool_call',
        tool_name: 'search_in_issues',
        args: { query: 'Is item 1 still active?' },
        result: { status: 'ok', content: {} },
      },
    }
    const wrapper = await mount(
      [step(1, { status: 'ok', content: { tables: [] } }), search],
      false
    )
    await wrapper.find('.agent-chat-tool-group__header').trigger('click')
    expect(
      wrapper
        .findAll('.agent-chat-tool-group__step-summary')
        .map((summary) => summary.text())
    ).toEqual(['Enable row creation', 'Is item 1 still active?'])
  })
})
