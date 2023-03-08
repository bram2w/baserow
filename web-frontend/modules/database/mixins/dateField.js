import moment from '@baserow/modules/core/moment'
import {
  getDateMomentFormat,
  getTimeMomentFormat,
  getDateHumanReadableFormat,
  getTimeHumanReadableFormat,
  getFieldTimezone,
  getCellTimezoneAbbr,
} from '@baserow/modules/database/utils/date'

const DATE_PICKER_FORMAT = 'YYYY-MM-DD'

/**
 * Mixin that introduces methods for the date field. This can both be used for a row
 * and grid view field.
 */
export default {
  data() {
    return {
      date: '',
      pickerDate: '',
      time: '',
      momentDate: null,
    }
  },
  computed: {
    /**
     * We need to watch the value and the date/time formats. This can easily be done
     * with a computed property.
     */
    valueAndFormats() {
      return `${this.value}|${this.field.date_format}|${this.field.date_time_format}|${this.field.date_force_timezone}`
    },
    fieldDateFormat() {
      return getDateMomentFormat(this.field.date_format)
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
    updateDateValue() {
      this.pickerDate = this.momentDate.format(DATE_PICKER_FORMAT)
      this.date = this.momentDate.format(this.fieldDateFormat)
    },
    updateTimeValue() {
      const timeFormat = getTimeMomentFormat(this.field.date_time_format)
      this.time = this.momentDate.format(timeFormat)
    },
    /**
     * When the date part is updated we also need to update the copy data which
     * contains the whole date(time) in the correct format. The copy contains the
     * value that is actually going to be saved.
     */
    updateDate(field, value) {
      const dateFormats = [DATE_PICKER_FORMAT, this.fieldDateFormat]
      const timezone = getFieldTimezone(field)
      let newDate = moment.utc(value, dateFormats, true)
      if (timezone !== null) {
        newDate = newDate.clone().tz(timezone, true)
      }

      if (newDate.isValid()) {
        this.updateCopy(field, {
          year: newDate.year(),
          month: newDate.month(),
          date: newDate.date(),
        })
        this.updateDateValue()
      } else {
        this.date = value
      }
    },
    /**
     * When the time part is updated we also need to update the copy data which
     * contains the whole date(time) in the correct format. The copy contains the
     * value that is actually going to be saved.
     */
    updateTime(field, value) {
      const timeFormats = ['hh:mm a', 'HH:mm']
      const timezone = getFieldTimezone(field)
      let newTime = moment.utc(value, timeFormats, true)
      if (timezone !== null) {
        newTime = newTime.clone().tz(timezone, true)
      }

      if (newTime.isValid()) {
        this.updateCopy(field, {
          hour: newTime.hour(),
          minute: newTime.minute(),
          second: 0,
        })
        this.updateTimeValue()
      } else {
        this.time = value
      }
    },
    /**
     * When the user uses the datepicker to choose a date, we also need to update
     * date data and the copy so that the correct date is visible for the user.
     */
    chooseDate(field, value) {
      const timezone = getFieldTimezone(field)
      let pickerDate = moment.utc(value)
      if (timezone !== null) {
        pickerDate = pickerDate.clone().tz(timezone, true)
      }
      this.updateDate(field, pickerDate.format(DATE_PICKER_FORMAT))
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
    updateCopy(field, values) {
      const existing = this.momentDate.set(values)
      this.copy = field.date_include_time
        ? existing.format()
        : existing.format('YYYY-MM-DD')
    },
    /**
     * Updates the date and time data by converting the value to the correct formats.
     */
    setDateAndTime(field, value) {
      const timezone = getFieldTimezone(field)
      if (value === null) {
        this.date = this.time = ''
        this.momentDate = moment.utc()
        if (timezone) {
          this.momentDate = this.momentDate
            .clone()
            .utcOffset(moment.tz(timezone).utcOffset())
        }
        this.pickerDate = ''
        return
      }

      let existing = moment.utc(value, moment.ISO_8601, true)
      if (timezone) {
        existing = existing.clone().utcOffset(moment.tz(timezone).utcOffset())
      }

      this.momentDate = existing
      this.updateDateValue()
      this.updateTimeValue()
    },
    getCellTimezoneAbbr(field, value, force) {
      return getCellTimezoneAbbr(field, value, { force })
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
