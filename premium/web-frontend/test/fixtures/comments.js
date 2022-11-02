export function thereAreComments(mock, comments, tableId, rowId) {
  mock.onGet(/row_comments\/.+\/.+/).reply(200, {
    results: comments,
  })
}
