/**
 * Registers the real time events related to the baserow_premium module. When a message
 * comes in, the state of the stores will be updated to match the latest update.
 */
export const registerRealtimeEvents = (realtime) => {
  realtime.registerEvent('row_comment_created', ({ store }, data) => {
    store.dispatch('row_comments/forceCreate', data.row_comment)
  })
}
