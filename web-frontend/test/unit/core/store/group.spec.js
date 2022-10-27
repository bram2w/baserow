import groupStore from '@baserow/modules/core/store/group'
import { TestApp } from '@baserow/test/helpers/testApp'
import { expect } from '@jest/globals'

describe('Group store', () => {
  let testApp = null
  let store = null

  beforeEach(() => {
    testApp = new TestApp()
    store = testApp.store
  })

  afterEach(() => {
    testApp.afterEach()
  })

  test('forceAddGroupUser adds user to a group', async () => {
    const state = Object.assign(groupStore.state(), {
      items: [
        {
          id: 1,
          name: 'Group 1',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 73,
              user_id: 256,
              group: 1,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
      ],
    })
    groupStore.state = () => state
    store.registerModule('test', groupStore)

    await store.dispatch('test/forceAddGroupUser', {
      groupId: 1,
      values: {
        id: 74,
        user_id: 257,
        group: 1,
        name: 'Adam',
        email: 'adam@example.com',
        permissions: 'MEMBER',
        to_be_deleted: false,
        created_on: '2022-08-10T14:20:05.629890Z',
      },
    })

    const group = store.getters['test/get'](1)
    expect(group.users.length).toBe(2)
    expect(group.users[1].user_id).toBe(257)
    expect(group.users[1].permissions).toBe('MEMBER')
  })

  test('forceUpdateGroupUser updates a user from the group', async () => {
    const state = Object.assign(groupStore.state(), {
      items: [
        {
          id: 1,
          name: 'Group 1',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 73,
              user_id: 256,
              group: 1,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
      ],
    })
    groupStore.state = () => state
    store.registerModule('test', groupStore)

    await store.dispatch('test/forceUpdateGroupUser', {
      groupId: 1,
      id: 73,
      values: {
        id: 73,
        user_id: 256,
        group: 1,
        name: 'Petr',
        email: 'petr@example.com',
        permissions: 'MEMBER',
        to_be_deleted: false,
        created_on: '2022-08-10T14:20:05.629890Z',
      },
    })

    const group = store.getters['test/get'](1)
    expect(group.users.length).toBe(1)
    expect(group.users[0].name).toBe('Petr')
    expect(group.users[0].permissions).toBe('MEMBER')
  })

  test(`forceUpdateGroupUser updates a current group permissions 
        when the current user is updated`, async () => {
    await store.dispatch('auth/forceSetUserData', {
      user: {
        id: 256,
      },
      access_token:
        `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImpvaG5AZXhhb` +
        `XBsZS5jb20iLCJpYXQiOjE2NjAyOTEwODYsImV4cCI6MTY2MDI5NDY4NiwianRpIjo` +
        `iNDZmNzUwZWUtMTJhMS00N2UzLWJiNzQtMDIwYWM4Njg3YWMzIiwidXNlcl9pZCI6M` +
        `iwidXNlcl9wcm9maWxlX2lkIjpbMl0sIm9yaWdfaWF0IjoxNjYwMjkxMDg2fQ.RQ-M` +
        `NQdDR9zTi8CbbQkRrwNsyDa5CldQI83Uid1l9So`,
    })
    const state = Object.assign(groupStore.state(), {
      items: [
        {
          id: 1,
          name: 'Group 1',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 73,
              user_id: 256,
              group: 1,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
      ],
    })
    groupStore.state = () => state
    store.registerModule('test', groupStore)

    await store.dispatch('test/forceUpdateGroupUser', {
      groupId: 1,
      id: 73,
      values: {
        id: 73,
        user_id: 256,
        group: 1,
        name: 'Petr',
        email: 'petr@example.com',
        permissions: 'MEMBER',
        to_be_deleted: false,
        created_on: '2022-08-10T14:20:05.629890Z',
      },
    })

    const group = store.getters['test/get'](1)
    expect(group.users.length).toBe(1)
    expect(group.users[0].name).toBe('Petr')
    expect(group.users[0].permissions).toBe('MEMBER')

    expect(group.permissions).toBe('MEMBER')
  })

  test('forceUpdateGroupUserAttributes updates a user across all groups', async () => {
    const state = Object.assign(groupStore.state(), {
      items: [
        {
          id: 1,
          name: 'Group 1',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 73,
              user_id: 256,
              group: 1,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
        {
          id: 2,
          name: 'Group 2',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 2136,
              user_id: 456,
              group: 2,
              name: 'Peter',
              email: 'peter@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
            {
              id: 173,
              user_id: 256,
              group: 2,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
        {
          id: 3,
          name: 'Group 3',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 2132,
              user_id: 456,
              group: 3,
              name: 'Peter',
              email: 'peter@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
      ],
    })
    groupStore.state = () => state
    store.registerModule('test', groupStore)

    await store.dispatch('test/forceUpdateGroupUserAttributes', {
      userId: 256,
      values: {
        name: 'John renamed',
        to_be_deleted: true,
      },
    })

    const group = store.getters['test/get'](1)
    expect(group.users[0].name).toBe('John renamed')
    expect(group.users[0].to_be_deleted).toBe(true)

    const group2 = store.getters['test/get'](2)
    expect(group2.users[0].name).toBe('Peter')
    expect(group2.users[0].to_be_deleted).toBe(false)
    expect(group2.users[1].name).toBe('John renamed')
    expect(group2.users[1].to_be_deleted).toBe(true)

    const group3 = store.getters['test/get'](3)
    expect(group3.users[0].name).toBe('Peter')
    expect(group3.users[0].to_be_deleted).toBe(false)
  })

  test('forceDeleteGroupUser removes a user from the group', async () => {
    const state = Object.assign(groupStore.state(), {
      items: [
        {
          id: 1,
          name: 'Group 1',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 73,
              user_id: 256,
              group: 1,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
      ],
    })
    groupStore.state = () => state
    store.registerModule('test', groupStore)

    await store.dispatch('test/forceDeleteGroupUser', {
      groupId: 1,
      id: 73,
      values: {
        id: 73,
        user_id: 256,
        group: 1,
        name: 'John',
        email: 'john@example.com',
        permissions: 'ADMIN',
        to_be_deleted: false,
        created_on: '2022-08-10T14:20:05.629890Z',
      },
    })

    const group = store.getters['test/get'](1)
    expect(group.users.length).toBe(0)
  })

  test(`forceDeleteGroupUser removes the whole group if the 
        current user is being removed`, async () => {
    await store.dispatch('auth/forceSetUserData', {
      user: {
        id: 256,
      },
      access_token:
        `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImpvaG5AZXhhb` +
        `XBsZS5jb20iLCJpYXQiOjE2NjAyOTEwODYsImV4cCI6MTY2MDI5NDY4NiwianRpIjo` +
        `iNDZmNzUwZWUtMTJhMS00N2UzLWJiNzQtMDIwYWM4Njg3YWMzIiwidXNlcl9pZCI6M` +
        `iwidXNlcl9wcm9maWxlX2lkIjpbMl0sIm9yaWdfaWF0IjoxNjYwMjkxMDg2fQ.RQ-M` +
        `NQdDR9zTi8CbbQkRrwNsyDa5CldQI83Uid1l9So`,
    })

    const state = Object.assign(groupStore.state(), {
      items: [
        {
          id: 1,
          name: 'Group 1',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 73,
              user_id: 256,
              group: 1,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
      ],
    })
    groupStore.state = () => state
    store.registerModule('test', groupStore)

    await store.dispatch('test/forceDeleteGroupUser', {
      groupId: 1,
      id: 73,
      values: {
        id: 73,
        user_id: 256,
        group: 1,
        name: 'John',
        email: 'john@example.com',
        permissions: 'ADMIN',
        to_be_deleted: false,
        created_on: '2022-08-10T14:20:05.629890Z',
      },
    })

    const groups = store.getters['test/getAll']
    expect(groups.length).toBe(0)
  })

  test('forceDeleteUser deletes all group users across all groups', async () => {
    const state = Object.assign(groupStore.state(), {
      items: [
        {
          id: 1,
          name: 'Group 1',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 73,
              user_id: 256,
              group: 1,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
        {
          id: 2,
          name: 'Group 2',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 2136,
              user_id: 456,
              group: 2,
              name: 'Peter',
              email: 'peter@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
            {
              id: 173,
              user_id: 256,
              group: 2,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
        {
          id: 3,
          name: 'Group 3',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 2132,
              user_id: 456,
              group: 3,
              name: 'Peter',
              email: 'peter@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
      ],
    })
    groupStore.state = () => state
    store.registerModule('test', groupStore)

    await store.dispatch('test/forceDeleteUser', {
      userId: 256,
    })

    const group = store.getters['test/get'](1)
    expect(group.users.length).toBe(0)

    const group2 = store.getters['test/get'](2)
    expect(group2.users[0].name).toBe('Peter')
    expect(group2.users[0].to_be_deleted).toBe(false)
    expect(group2.users.length).toBe(1)

    const group3 = store.getters['test/get'](3)
    expect(group3.users.length).toBe(1)
  })

  test('getAllUsers collects users from all groups', async () => {
    const state = Object.assign(groupStore.state(), {
      items: [
        {
          id: 1,
          name: 'Group 1',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 73,
              user_id: 256,
              group: 1,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
        {
          id: 2,
          name: 'Group 2',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 2136,
              user_id: 456,
              group: 2,
              name: 'Peter',
              email: 'peter@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
            {
              id: 173,
              user_id: 256,
              group: 2,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
        {
          id: 3,
          name: 'Group 3',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 2144,
              user_id: 556,
              group: 3,
              name: 'Mark',
              email: 'mark@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
      ],
    })
    groupStore.state = () => state
    store.registerModule('test', groupStore)

    const allUsers = await store.getters['test/getAllUsers']
    expect(allUsers[256].name).toBe('John')
    expect(allUsers[456].name).toBe('Peter')
    expect(allUsers[556].name).toBe('Mark')
  })

  test('getAllUsersByEmail collects users by email from all groups', async () => {
    const state = Object.assign(groupStore.state(), {
      items: [
        {
          id: 1,
          name: 'Group 1',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 73,
              user_id: 256,
              group: 1,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
        {
          id: 2,
          name: 'Group 2',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 2136,
              user_id: 456,
              group: 2,
              name: 'Peter',
              email: 'peter@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
            {
              id: 173,
              user_id: 256,
              group: 2,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
        {
          id: 3,
          name: 'Group 3',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 2144,
              user_id: 556,
              group: 3,
              name: 'Mark',
              email: 'mark@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
      ],
    })
    groupStore.state = () => state
    store.registerModule('test', groupStore)

    const allUsers = await store.getters['test/getAllUsersByEmail']
    expect(allUsers['john@example.com'].name).toBe('John')
    expect(allUsers['peter@example.com'].name).toBe('Peter')
    expect(allUsers['mark@example.com'].name).toBe('Mark')
  })

  test('getUserById returns user by id from any of the groups', async () => {
    const state = Object.assign(groupStore.state(), {
      items: [
        {
          id: 1,
          name: 'Group 1',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 73,
              user_id: 256,
              group: 1,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
        {
          id: 2,
          name: 'Group 2',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 2136,
              user_id: 456,
              group: 2,
              name: 'Peter',
              email: 'peter@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
            {
              id: 173,
              user_id: 256,
              group: 2,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
        {
          id: 3,
          name: 'Group 3',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 2144,
              user_id: 556,
              group: 3,
              name: 'Mark',
              email: 'mark@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
      ],
    })
    groupStore.state = () => state
    store.registerModule('test', groupStore)

    const mark = await store.getters['test/getUserById'](556)
    expect(mark.name).toBe('Mark')
  })

  test('getUserByEmail returns user by email from any of the groups', async () => {
    const state = Object.assign(groupStore.state(), {
      items: [
        {
          id: 1,
          name: 'Group 1',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 73,
              user_id: 256,
              group: 1,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
        {
          id: 2,
          name: 'Group 2',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 2136,
              user_id: 456,
              group: 2,
              name: 'Peter',
              email: 'peter@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
            {
              id: 173,
              user_id: 256,
              group: 2,
              name: 'John',
              email: 'john@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
        {
          id: 3,
          name: 'Group 3',
          order: 1,
          permissions: 'ADMIN',
          users: [
            {
              id: 2144,
              user_id: 556,
              group: 3,
              name: 'Mark',
              email: 'mark@example.com',
              permissions: 'ADMIN',
              to_be_deleted: false,
              created_on: '2022-08-10T14:20:05.629890Z',
            },
          ],
        },
      ],
    })
    groupStore.state = () => state
    store.registerModule('test', groupStore)

    const mark = await store.getters['test/getUserByEmail']('mark@example.com')
    expect(mark.name).toBe('Mark')
  })
})
