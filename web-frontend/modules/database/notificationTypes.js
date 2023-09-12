import { NotificationType } from '@baserow/modules/core/notificationTypes'
import NotificationSenderInitialsIcon from '@baserow/modules/core/components/notifications/NotificationSenderInitialsIcon'
import CollaboratorAddedToRowNotification from '@baserow/modules/database/components/notifications/CollaboratorAddedToRowNotification'

export class CollaboratorAddedToRowNotificationType extends NotificationType {
  static getType() {
    return 'collaborator_added_to_row'
  }

  getIconComponent() {
    return NotificationSenderInitialsIcon
  }

  getContentComponent() {
    return CollaboratorAddedToRowNotification
  }
}
