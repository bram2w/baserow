import { getRealtimeRecoveryRequestConfig } from '@baserow/modules/core/plugins/realtimeProtocol'

export default (client) => {
  return {
    fetchAll({ tableId, rowId, limit, offset, realtimeRecovery = false }) {
      return client.get(`/database/rows/table/${tableId}/${rowId}/history/`, {
        ...(realtimeRecovery ? getRealtimeRecoveryRequestConfig() : {}),
        params: {
          limit,
          offset,
        },
      })
    },
  }
}
