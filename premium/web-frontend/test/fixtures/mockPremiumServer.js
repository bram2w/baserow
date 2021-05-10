import {
  aUser,
  createUsersForAdmin,
  expectUserDeleted,
  expectUserUpdated,
  expectUserUpdatedRespondsWithError,
} from './user'

export default class MockPremiumServer {
  constructor(mock) {
    this.mock = mock
  }

  thereAreUsers(users, page, options = {}) {
    createUsersForAdmin(this.mock, users, page, options)
  }

  aUser(user = {}) {
    return aUser(user)
  }

  expectUserDeleted(userId) {
    expectUserDeleted(this.mock, userId)
  }

  expectUserUpdated(user, changes) {
    expectUserUpdated(this.mock, user, changes)
  }

  expectUserUpdatedRespondsWithError(user, error) {
    expectUserUpdatedRespondsWithError(this.mock, user, error)
  }
}
