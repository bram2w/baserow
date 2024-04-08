<script>
import notificationService from '@baserow/modules/core/services/notification'

/**
 * This page functions as a never changing path in the web-frontend that will redirect
 * the visitor to the correct page related to the provided notification type and ID.
 * The reason we have this is so that the backend doesn't need to know about the paths
 * available in the web-frontend, and won't break behavior if they change.
 */
export default {
  async asyncData({ route, redirect, app, error, store }) {
    let notification

    try {
      const { data } = await notificationService(app.$client).markAsRead(
        route.params.workspaceId,
        route.params.notificationId
      )
      notification = data
    } catch {
      return error({ statusCode: 404, message: 'Notification not found.' })
    }

    const notificationType = app.$registry.get(
      'notification',
      notification.type
    )
    const redirectParams = notificationType.getRoute(notification.data)

    if (!redirectParams) {
      return error({ statusCode: 404, message: 'Notification has no route.' })
    }

    return redirect(redirectParams)
  },
}
</script>
