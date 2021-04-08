export function createApplication(
  mock,
  { applicationId = 1, groupId = 1, tables = [] }
) {
  const application = {
    id: applicationId,
    name: 'Test Database App',
    order: applicationId,
    type: 'database',
    group: {
      id: groupId,
      name: 'Test group',
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
