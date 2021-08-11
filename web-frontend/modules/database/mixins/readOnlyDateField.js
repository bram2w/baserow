import moment from '@baserow/modules/core/moment'
import {
  getDateMomentFormat,
  getTimeMomentFormat,
} from '@baserow/modules/database/utils/date'

export default {
  methods: {
    getTimezone(field) {
      return field.timezone || 'UTC'
    },
    getDate(field, value) {
      if (value === null) {
        return ''
      }

      const existing = moment.tz(value || undefined, this.getTimezone(field))
      const dateFormat = getDateMomentFormat(field.date_format)
      return existing.format(dateFormat)
    },
    getTime(field, value) {
      if (value === null) {
        return ''
      }

      const existing = moment.tz(value || undefined, this.getTimezone(field))
      const timeFormat = getTimeMomentFormat(field.date_time_format)
      return existing.format(timeFormat)
    },
  },
}
