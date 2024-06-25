import {
  aUser,
  createUsersForAdmin,
  expectUserDeleted,
  expectUserUpdated,
  expectUserUpdatedRespondsWithError,
} from './user'
import { thereAreComments } from './comments'
import { createKanbanView, thereAreRowsInKanbanView } from './kanban'
import { MockServer } from '@baserow/test/fixtures/mockServer'

export default class MockPremiumServer extends MockServer {
  createKanbanView(
    application,
    table,
    {
      filters = [],
      sortings = [],
      groupBys = [],
      decorations = [],
      singleSelectFieldId = -1,
      ...rest
    }
  ) {
    return createKanbanView(this.mock, application, table, {
      filters,
      sortings,
      groupBys,
      decorations,
      singleSelectFieldId,
      ...rest,
    })
  }

  thereAreUsers(users, page, options = {}) {
    createUsersForAdmin(this.mock, users, page, options)
  }

  thereAreRowsInKanbanView(fieldOptions, rows) {
    thereAreRowsInKanbanView(this.mock, fieldOptions, rows)
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
