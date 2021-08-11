/**
 * Registers the real time events related to the baserow_premium module. When a message
 * comes in, the state of the stores will be updated to match the latest update.
 */

export const registerRealtimeEvents = (realtime) => {
  realtime.registerEvent('row_comment_created', async ({ store }, data) => {
    const rowComment = data.row_comment
    await store.dispatch('row_comments/forceCreate', {
      rowComment,
    })
  })
}
