export default (client) => {
  return {
    fetchAll({ tableId, rowId }) {
      // mocked for now
      return {
        data: {
          count: 2,
          next: null,
          previous: null,
          results: [
            {
              id: 1,
              action_type: 'update_row',
              user: {
                id: 1,
                name: 'John Wick',
              },
              timestamp: '2023-08-09T00:30:00Z',
              before: {
                field_1: 'a',
              },
              after: {
                field_1: 'aa',
              },
            },
            {
              id: 2,
              action_type: 'update_row',
              user: {
                id: 2,
                name: 'Paul Smith',
              },
              timestamp: '2023-08-09T00:30:00Z',
              before: {
                field_2: 'a',
              },
              after: {
                field_1: 'aa',
                field_2: 'a',
              },
            },
          ],
        },
      }
    },
  }
}
