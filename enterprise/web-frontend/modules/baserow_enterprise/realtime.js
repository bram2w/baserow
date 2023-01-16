/**
 * Registers the real time events related to the baserow_enterprise module. When a message
 * comes in, the state of the stores will be updated to match the latest update.
 */

export const registerRealtimeEvents = (realtime) => {
  realtime.registerEvent(
    'permissions_updated',
    ({ store }, { group_id: groupId }) => {
      if (store.getters['group/haveGroupPermissionsBeenLoaded'](groupId)) {
        store.dispatch('notification/setPermissionsUpdated', true)
      }
    }
  )
}
