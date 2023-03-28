export function createApplication(
  mock,
  { applicationId = 1, workspaceId = 1, tables = [] }
) {
  const application = {
    id: applicationId,
    name: 'Test Database App',
    order: applicationId,
    type: 'database',
    workspace: {
      id: workspaceId,
      name: 'Test workspace',
    },
    tables: tables.map((t) => ({
      ...t,
      count: t.id,
      database_id: applicationId,
    })),
  }
  mock.onGet('/applications/').reply(200, [application])
  return application
}
