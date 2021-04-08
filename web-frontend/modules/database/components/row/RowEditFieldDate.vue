<template>
  <div class="control__elements">
    <div class="field-date__container">
      <div class="input__with-icon field-date">
        <input
          ref="date"
          v-model="date"
          type="text"
          class="input input--large"
          :placeholder="getDatePlaceholder(field)"
          :disabled="readOnly"
          @keyup.enter="$refs.date.blur()"
          @keyup="updateDate(field, date)"
          @focus="focus($refs.dateContext, $event)"
          @blur="blur($refs.dateContext, $event)"
        />
        <i class="fas fa-calendar-check"></i>
        <Context
          ref="dateContext"
          :hide-on-click-outside="false"
          class="datepicker-context"
        >
          <client-only>
            <date-picker
              v-if="!readOnly"
              :inline="true"
              :monday-first="true"
              :use-utc="true"
              :value="copy"
              class="datepicker"
              @input="chooseDate(field, $event)"
            ></date-picker>
          </client-only>
        </Context>
      </div>
      <div
        v-if="field.date_include_time"
        class="input__with-icon field-date__time"
      >
        <input
          ref="time"
          v-model="time"
          type="text"
          class="input input--large"
          :placeholder="getTimePlaceholder(field)"
          :disabled="readOnly"
          @keyup.enter="$refs.time.blur()"
          @keyup="updateTime(field, time)"
          @focus="focus($refs.timeContext, $event)"
          @blur="blur($refs.timeContext, $event)"
        />
        <i class="fas fa-clock"></i>
        <TimeSelectContext
          v-if="!readOnly"
          ref="timeContext"
          :value="time"
          :hide-on-click-outside="false"
          :notation="field.date_time_format"
          @input="chooseTime(field, $event)"
        ></TimeSelectContext>
      </div>
    </div>
  </div>
</template>

<script>
import TimeSelectContext from '@baserow/modules/core/components/TimeSelectContext'
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import rowEditFieldInput from '@baserow/modules/database/mixins/rowEditFieldInput'
import dateField from '@baserow/modules/database/mixins/dateField'

export default {
  components: { TimeSelectContext },
  mixins: [rowEditField, rowEditFieldInput, dateField],
  methods: {
    focus(...args) {
      this.select()
      dateField.methods.focus.call(this, ...args)
    },
    blur(...args) {
      dateField.methods.blur.call(this, ...args)
      this.unselect()
    },
  },
}
</script>
