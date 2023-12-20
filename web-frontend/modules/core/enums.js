export const IMAGE_FILE_TYPES = ['image/jpeg', 'image/jpg', 'image/png']

// Keep these in sync with the backend options in
// baserow.core.models.UserProfile.EmailNotificationFrequencyOptions
export const EMAIL_NOTIFICATIONS_FREQUENCY_OPTIONS = {
  INSTANT: 'instant',
  DAILY: 'daily',
  WEEKLY: 'weekly',
  NEVER: 'never',
}

export const DATA_TYPE_TO_ICON_MAP = {
  string: 'iconoir-text',
  number: 'baserow-icon-hashtag',
  boolean: 'baserow-icon-circle-checked',
}

export const UNKNOWN_DATA_TYPE_ICON = 'iconoir-question-mark'
