import { AgentChatRolePermissionManagerType } from '@baserow_enterprise/permissionManagerTypes'

describe('AgentChatRolePermissionManagerType', () => {
  const manager = new AgentChatRolePermissionManagerType({})
  const permissions = {
    default: ['EDITOR'],
    applications: { 1: ['BUILDER'] },
  }

  test('only denies below the minimum role', () => {
    const application = { id: 1, start_chat_min_role: 'BUILDER' }
    expect(
      manager.hasPermission(
        permissions,
        'agent_application.start_chat',
        application
      )
    ).toBe(null)
    expect(
      manager.hasPermission(permissions, 'agent_application.start_chat', {
        ...application,
        start_chat_min_role: 'ADMIN',
      })
    ).toBe(false)
    expect(
      manager.hasPermission(permissions, 'agent_application.start_chat', {
        ...application,
        start_chat_min_role: 'NOBODY',
      })
    ).toBe(false)
  })

  test('falls back to the workspace roles for applications created later', () => {
    expect(
      manager.hasPermission(
        permissions,
        'agent_application.continue_triggered_chat',
        { id: 2, continue_chat_min_role: 'BUILDER' }
      )
    ).toBe(false)
  })

  test('passes other operations and the default minimum role through', () => {
    expect(
      manager.hasPermission(permissions, 'agent_application.run_chat', {
        id: 1,
      })
    ).toBe(null)
    expect(
      manager.hasPermission(permissions, 'agent_application.start_chat', {
        id: 2,
        start_chat_min_role: 'EDITOR',
      })
    ).toBe(null)
  })
})
