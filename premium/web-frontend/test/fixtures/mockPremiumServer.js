import {
  aUser,
  createUsersForAdmin,
  expectUserDeleted,
  expectUserUpdated,
  expectUserUpdatedRespondsWithError,
} from './user'
import { thereAreComments } from './comments'

export default class MockPremiumServer {
  constructor(mock) {
    this.mock = mock
  }

  thereAreUsers(users, page, options = {}) {
    createUsersForAdmin(this.mock, users, page, options)
  }

  thereAreComments(comments, tableId, rowId) {
    thereAreComments(this.mock, comments, tableId, rowId)
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

  expectPremiumViewUpdate(viewId, expectedContents) {
    this.mock
      .onPatch(`/database/view/${viewId}/premium`, expectedContents)
      .reply(200, expectedContents)
  }
}
