import moment from '@baserow/modules/core/moment'
import {
  getDateMomentFormat,
  getTimeMomentFormat,
  getDateHumanReadableFormat,
  getTimeHumanReadableFormat,
} from '@baserow/modules/database/utils/date'

/**
 * Mixin that introduces methods for the date field. This can both be used for a row
 * and grid view field.
 */
export default {
  data() {
    return {
      date: '',
      time: '',
    }
  },
  computed: {
    /**
     * We need to watch the value and the date/time formats. This can easily be done
     * with a computed property.
     */
    valueAndFormats() {
      return `${this.value}|${this.field.date_format}|${this.field.date_time_format}`
    },
  },
  watch: {
    /**
     * When the value or one of the date formats changes we need to update the date
     * and time data with the correct values. This is because the date and time data
     * are directly visible to the user and not the value like most other fields.
     */
    valueAndFormats() {
      if (!this.editing) {
        this.setDateAndTime(this.field, this.value)
      }
    },
  },
  created() {
    this.setDateAndTime(this.field, this.value)
  },
  methods: {
    /**
     * When the date part is updated we also need to update the copy data which
     * contains the whole date(time) in the correct format. The copy contains the
     * value that is actually going to be saved.
     */
    updateDate(field, value) {
      const dateFormat = getDateMomentFormat(field.date_format)
      const newDate = moment.utc(value, dateFormat)
      this.updateCopy(
        field,
        {
          year: newDate.year(),
          month: newDate.month(),
          date: newDate.date(),
        },
        newDate
      )
    },
    /**
     * When the time part is updated we also need to update the copy data which
     * contains the whole date(time) in the correct format. The copy contains the
     * value that is actually going to be saved.
     */
    updateTime(field, value) {
      const newTime = moment.utc(value, ['h:m a', 'H:m'])
      this.updateCopy(
        field,
        {
          hour: newTime.hour(),
          minute: newTime.minute(),
          second: 0,
        },
        newTime
      )
    },
    /**
     * When the user uses the datapicker to choose a date, we also need to update
     * date data and the copy so that the correct date is visible for the user.
     */
    chooseDate(field, value) {
      const dateFormat = getDateMomentFormat(field.date_format)
      value = moment.utc(value).format(dateFormat)
      this.date = value
      this.updateDate(field, value)
    },
    /**
     * When the user uses the time context to choose a time, we also need to update
     * time data and the copy so that the correct time is visible for the user.
     */
    chooseTime(field, value) {
      this.updateTime(field, value)
      this.time = value
    },
    /**
     * A helper method that allows updating the copy data by only changing certain
     * properties of a datetime. For example only the month could be updated.
     */
    updateCopy(field, values, newDate) {
      if (!newDate.isValid()) {
        return
      }

      const existing = moment.utc(this.copy || undefined)
      existing.set(values)
      let newValue = existing.format()
      if (!field.date_include_time) {
        newValue = existing.format('YYYY-MM-DD')
      }
      this.copy = newValue
    },
    /**
     * Updates the date and time data by converting the value to the correct formats.
     */
    setDateAndTime(field, value) {
      if (value === null) {
        this.date = ''
        this.time = ''
        return
      }

      const existing = moment.utc(value || undefined)

      const dateFormat = getDateMomentFormat(this.field.date_format)
      const timeFormat = getTimeMomentFormat(this.field.date_time_format)

      this.date = existing.format(dateFormat)
      this.time = existing.format(timeFormat)
    },
    /**
     * Returns a human readable date placeholder of the format for the input.
     */
    getDatePlaceholder(field) {
      return this.$t(
        'humanDateFormat.' + getDateHumanReadableFormat(field.date_format)
      )
    },
    /**
     * Returns a human readable time placeholder of the format for the input.
     */
    getTimePlaceholder(field) {
      return getTimeHumanReadableFormat(field.date_time_format)
    },
    /**
     * When the user focuses on one of the inputs the related context menu must
     * also be opened.
     */
    focus(context, event) {
      context.toggle(event.currentTarget, 'bottom', 'left', 0)
    },
    /**
     * When the user blurs one of the inputs the related context menu must also be
     * hidden.
     */
    blur(context, event) {
      context.hide()
    },
  },
}
