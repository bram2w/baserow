import {
  approvalActsAsUser,
  hasMoreAccess,
  workspaceToolIdentities,
  listToolIdentityExceptions,
} from '@baserow_enterprise/utils/agentToolIdentities'

const investor = { id: 1, name: 'Investor', role_uid: 'BUILDER' }
const outreach = { id: 2, name: 'Baserow Outreach', role_uid: 'EDITOR' }
const admin = { id: 3, name: 'Admin', role_uid: 'ADMIN' }

describe('agentToolIdentities', () => {
  test('flags identities with more access than the agent', () => {
    expect(hasMoreAccess(outreach, investor)).toBe(false)
    expect(hasMoreAccess(admin, investor)).toBe(true)
    expect(hasMoreAccess(outreach, null)).toBe(true)
    expect(hasMoreAccess({ id: 4, role_uid: 'custom' }, investor)).toBe(false)
  })

  test('normalizes the tool identities of a config', () => {
    expect(
      workspaceToolIdentities({ tool_identities: { a: 2, b: '3', c: 'x' } })
    ).toEqual({ a: 2, b: 3 })
    expect(workspaceToolIdentities(undefined)).toEqual({})
  })

  test('lists workspace and action tool exceptions', () => {
    const exceptions = listToolIdentityExceptions({
      workspaceTool: {
        config: { tool_identities: { list_rows: 2, gone: 99 } },
      },
      actionTools: [
        { id: 7, type: 'service', name: 'Send an email', identity_id: 2 },
        { id: 8, type: 'service', name: 'Slack', identity_id: null },
      ],
      catalog: [{ name: 'list_rows', label: 'Read rows' }],
      identities: [investor, outreach],
    })
    expect(
      exceptions.map((item) => [item.key, item.label, item.identity.id])
    ).toEqual([
      ['workspace-list_rows', 'Read rows', 2],
      ['action-7', 'Send an email', 2],
    ])
  })
})

describe('agentToolIdentities acting as the user', () => {
  test('keeps the user value in tool identities', () => {
    expect(
      workspaceToolIdentities({ tool_identities: { a: 'user', b: 2 } })
    ).toEqual({ a: 'user', b: 2 })
  })

  test('lists tools acting as the user only when asked to', () => {
    const options = {
      workspaceTool: { config: { tool_identities: { list_rows: 'user' } } },
      actionTools: [{ id: 7, name: 'Add row', act_as_user: true }],
      catalog: [{ name: 'list_rows', label: 'List rows' }],
      identities: [],
    }
    expect(listToolIdentityExceptions(options)).toEqual([])
    const exceptions = listToolIdentityExceptions({
      ...options,
      userIdentity: { name: 'The user' },
    })
    expect(exceptions.map((exception) => exception.label)).toEqual([
      'List rows',
      'Add row',
    ])
    expect(exceptions[0].identity).toEqual({ id: 'user', name: 'The user' })
  })
})

describe('approvalActsAsUser', () => {
  const catalog = [{ name: 'create_rows' }, { name: 'list_tables' }]
  const workspaceTool = (identities = {}) => ({
    type: 'workspace',
    config: { tool_identities: identities },
  })

  test('follows the workspace tool identities and the application', () => {
    const tools = [workspaceTool({ create_rows: 'user', list_tables: 3 })]
    const application = { act_as_user: false }
    expect(
      approvalActsAsUser('create_rows_in_table_12', {
        tools,
        catalog,
        application,
      })
    ).toBe(true)
    expect(
      approvalActsAsUser('list_tables', { tools, catalog, application })
    ).toBe(false)
    expect(
      approvalActsAsUser('list_tables', {
        tools: [workspaceTool()],
        catalog,
        application: { act_as_user: true },
      })
    ).toBe(true)
  })

  test('follows action tools and their own identity', () => {
    const application = { act_as_user: true }
    const tools = [
      { type: 'service', name: 'Add row', identity_id: null },
      { type: 'service', name: 'Mail', identity_id: 4 },
    ]
    expect(approvalActsAsUser('add_row', { tools, catalog, application })).toBe(
      true
    )
    expect(approvalActsAsUser('mail', { tools, catalog, application })).toBe(
      false
    )
    expect(approvalActsAsUser('unknown', { tools, catalog, application })).toBe(
      false
    )
  })
})
