export function createGroup(mock, { groupId = 1 }) {
  const group = {
    order: groupId,
    permissions: 'ADMIN',
    id: groupId,
    name: `group_${groupId}`,
  }
  mock.onGet('/groups/').reply(200, [group])
  return group
}
