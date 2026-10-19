import flushPromises from 'flush-promises'
import { TestApp } from '@baserow/test/helpers/testApp'
import McpOAuthConnections from '@baserow/modules/core/components/settings/McpOAuthConnections.vue'

describe('McpOAuthConnections', () => {
  let testApp = null

  const mcpUrl = 'https://api.example.com/mcp'
  const connections = [
    {
      id: 11,
      client_name: 'claude',
      verified: true,
      verified_host: 'claude.ai',
      workspace_id: 1,
      workspace_name: 'Sales',
      allowed_tools: ['list_tables', 'list_rows'],
      tool_count: 2,
      unavailable_tools: [],
      created: '2026-10-06T10:00:00Z',
    },
    {
      id: 12,
      client_name: 'Local client',
      verified: false,
      verified_host: null,
      workspace_id: 2,
      workspace_name: 'Ops',
      allowed_tools: ['list_tables'],
      tool_count: 1,
      unavailable_tools: ['delete_rows'],
      created: '2026-10-05T10:00:00Z',
    },
  ]

  const tools = [
    {
      name: 'list_tables',
      title: 'List tables',
      read_only: true,
      destructive: false,
      group: 'database_read',
    },
    {
      name: 'list_rows',
      title: 'List rows',
      read_only: true,
      destructive: false,
      group: 'database_read',
    },
    {
      name: 'create_rows',
      title: 'Create rows',
      read_only: false,
      destructive: false,
      group: 'database_edit',
    },
    {
      name: 'delete_rows',
      title: 'Delete rows',
      read_only: false,
      destructive: true,
      group: 'database_delete',
    },
  ]
  const groups = [
    {
      type: 'database_read',
      title: 'Read',
      area: 'database',
      read_only_preset: true,
    },
    {
      type: 'database_edit',
      title: 'Edit',
      area: 'database',
      read_only_preset: false,
    },
    {
      type: 'database_delete',
      title: 'Delete',
      area: 'database',
      read_only_preset: false,
    },
  ]
  const enabled = { oauth_enabled: true, mcp_url: mcpUrl, tools, groups }

  beforeEach(() => {
    testApp = new TestApp()
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  async function mount(data) {
    testApp.mock.onGet('/mcp/oauth/connections/').reply(200, data)
    const wrapper = await testApp.mount(McpOAuthConnections)
    await flushPromises()
    return wrapper
  }

  test('renders nothing and reports disabled when OAuth is off', async () => {
    const wrapper = await mount({
      oauth_enabled: false,
      mcp_url: null,
      connections: [],
    })
    expect(wrapper.find('.mcp-oauth-connections').exists()).toBe(false)
    expect(wrapper.emitted('loaded')).toEqual([[false]])
  })

  test('shows the URL and the client tabs', async () => {
    const wrapper = await mount({
      oauth_enabled: true,
      mcp_url: mcpUrl,
      connections: [],
    })
    expect(wrapper.emitted('loaded')).toEqual([[true]])
    expect(wrapper.find('[data-test="mcp-oauth-url"]').text()).toBe(mcpUrl)
    const text = wrapper.text()
    for (const title of ['Claude', 'Claude Code', 'ChatGPT', 'Cursor']) {
      expect(text).toContain(title)
    }
    expect(wrapper.find('[data-test="mcp-oauth-empty"]').exists()).toBe(true)
  })

  test('lists connections with badge, workspace and tool count', async () => {
    const wrapper = await mount({
      oauth_enabled: true,
      mcp_url: mcpUrl,
      connections,
    })
    const first = wrapper.find('[data-test="mcp-oauth-connection-11"]')
    const second = wrapper.find('[data-test="mcp-oauth-connection-12"]')
    expect(first.find('.mcp-oauth-connections__avatar').text()).toBe('C')
    expect(first.text()).toContain('claude')
    expect(first.text()).toContain('Sales')
    // The test i18n returns message keys.
    expect(first.text()).toContain('mcpOAuthConnections.tools')
    const badge = first.find('[data-test="mcp-oauth-published"]')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('mcpOAuthConnections.publishedBy')
    expect(badge.classes()).toContain('badge--neutral')
    expect(second.text()).toContain('Ops')
    expect(second.find('[data-test="mcp-oauth-published"]').exists()).toBe(
      false
    )
    expect(wrapper.find('[data-test="mcp-oauth-empty"]').exists()).toBe(false)
  })

  test('marks a connection whose sign-in expired', async () => {
    const wrapper = await mount({
      oauth_enabled: true,
      mcp_url: mcpUrl,
      connections: [{ ...connections[0], expired: true }, connections[1]],
    })
    const expired = (id) =>
      wrapper.find(
        `[data-test="mcp-oauth-connection-${id}"] [data-test="mcp-oauth-expired"]`
      )
    expect(expired(11).text()).toBe('mcpOAuthConnections.expired')
    expect(expired(11).classes()).toContain('badge--yellow')
    expect(expired(12).exists()).toBe(false)
  })

  test('disconnect asks once, then deletes and removes the row', async () => {
    const wrapper = await mount({
      oauth_enabled: true,
      mcp_url: mcpUrl,
      connections,
    })
    testApp.mock.onDelete('/mcp/oauth/connections/11/').reply(204)
    const row = () => wrapper.find('[data-test="mcp-oauth-connection-11"]')
    const button = () => row().find('[data-test="mcp-oauth-disconnect"]')

    await button().trigger('click')
    await flushPromises()
    expect(testApp.mock.history.delete.length).toBe(0)
    expect(button().text()).toBe('mcpOAuthConnections.confirmDisconnect')

    await button().trigger('click')
    await flushPromises()
    expect(testApp.mock.history.delete.map((r) => r.url)).toEqual([
      '/mcp/oauth/connections/11/',
    ])
    expect(row().exists()).toBe(false)
    expect(wrapper.find('[data-test="mcp-oauth-connection-12"]').exists()).toBe(
      true
    )
  })

  test('uses only its own block elements', async () => {
    const wrapper = await mount({
      oauth_enabled: true,
      mcp_url: mcpUrl,
      connections: [],
    })
    expect(wrapper.find('[class*="mcp-endpoint__"]').exists()).toBe(false)
    expect(wrapper.find('.mcp-oauth-connections__url-box').text()).toContain(
      '/mcp'
    )
  })

  // The test i18n drops message params; this `$t` keeps them in the text.
  const withParams = {
    global: {
      mocks: {
        $t: (key, params) =>
          params ? `${key} ${JSON.stringify(params)}` : key,
      },
    },
  }

  test('hints at the tools a connection could use but has off', async () => {
    testApp.mock
      .onGet('/mcp/oauth/connections/')
      .reply(200, { ...enabled, connections })
    const wrapper = await testApp.mount(McpOAuthConnections, withParams)
    await flushPromises()
    const hint = (id) =>
      wrapper.find(
        `[data-test="mcp-oauth-connection-${id}"] [data-test="mcp-oauth-tools-off"]`
      )
    // 11 has 2 of 4 on. 12 has 1 on and can't use delete_rows.
    expect(hint(11).text()).toContain('"count":2')
    expect(hint(12).text()).toContain('"count":2')
    testApp.mock.resetHandlers()
  })

  test('no hint when every usable tool is on', async () => {
    const wrapper = await mount({
      ...enabled,
      connections: [
        {
          ...connections[0],
          allowed_tools: ['list_tables', 'list_rows', 'create_rows'],
          unavailable_tools: ['delete_rows'],
        },
      ],
    })
    expect(wrapper.find('[data-test="mcp-oauth-tools-off"]').exists()).toBe(
      false
    )
  })

  test('edit tools saves the picked names and updates the row', async () => {
    const wrapper = await mount({ ...enabled, connections })
    testApp.mock
      .onPatch('/mcp/oauth/connections/11/', {
        allowed_tools: ['list_tables', 'list_rows', 'create_rows'],
      })
      .reply(200, {
        ...connections[0],
        allowed_tools: ['list_tables', 'list_rows', 'create_rows'],
        tool_count: 3,
      })
    await wrapper
      .find(
        '[data-test="mcp-oauth-connection-11"] [data-test="mcp-oauth-edit-tools"]'
      )
      .trigger('click')
    await flushPromises()
    const box = (name) =>
      document.querySelector(`[data-test="mcp-tool-picker-tool-${name}"] input`)
    expect(box('list_tables').checked).toBe(true)
    expect(box('create_rows').checked).toBe(false)
    box('create_rows').click()
    await flushPromises()
    document.querySelector('[data-test="mcp-oauth-save-tools"]').click()
    await flushPromises()
    expect(testApp.mock.history.patch.map((r) => JSON.parse(r.data))).toEqual([
      { allowed_tools: ['list_tables', 'list_rows', 'create_rows'] },
    ])
    expect(
      document.querySelector('[data-test="mcp-oauth-save-tools"]')
    ).toBeNull()
    expect(
      wrapper.vm.connections.find((c) => c.id === 11).allowed_tools
    ).toEqual(['list_tables', 'list_rows', 'create_rows'])
  })

  test('the tools modal hides tools the connection cannot use', async () => {
    const wrapper = await mount({ ...enabled, connections })
    await wrapper
      .find(
        '[data-test="mcp-oauth-connection-12"] [data-test="mcp-oauth-edit-tools"]'
      )
      .trigger('click')
    await flushPromises()
    expect(
      document.querySelector('[data-test="mcp-tool-picker-tool-delete_rows"]')
    ).toBeNull()
    expect(
      document.querySelector('[data-test="mcp-tool-picker-tool-create_rows"]')
    ).not.toBeNull()
  })

  test('save is disabled with no tool picked', async () => {
    const wrapper = await mount({ ...enabled, connections })
    await wrapper
      .find(
        '[data-test="mcp-oauth-connection-11"] [data-test="mcp-oauth-edit-tools"]'
      )
      .trigger('click')
    await flushPromises()
    document.querySelector('[data-test="mcp-tool-picker-none"]').click()
    await flushPromises()
    expect(
      document.querySelector('[data-test="mcp-oauth-save-tools"]').disabled
    ).toBe(true)
  })
})
