import { NotificationType } from '@baserow/modules/core/notificationTypes'
import RowCommentMentionNotification from '@baserow_premium/components/row_comments/RowCommentMentionNotification'
import NotificationSenderInitialsIcon from '@baserow/modules/core/components/notifications/NotificationSenderInitialsIcon'

export class RowCommentMentionNotificationType extends NotificationType {
  static getType() {
    return 'row_comment_mention'
  }

  getIconComponent() {
    return NotificationSenderInitialsIcon
  }

  getContentComponent() {
    return RowCommentMentionNotification
  }
}
