<template>
  <div>
    <div class="control">
      <label class="control__label control__label--small">{{
        $t('fieldDateSubForm.dateFormatLabel')
      }}</label>
      <div class="control__elements">
        <Dropdown
          v-model="values.date_format"
          :class="{ 'dropdown--error': $v.values.date_format.$error }"
          @hide="$v.values.date_format.$touch()"
        >
          <DropdownItem
            :name="$t('fieldDateSubForm.dateFormatEuropean') + ' (20/02/2020)'"
            value="EU"
          ></DropdownItem>
          <DropdownItem
            :name="$t('fieldDateSubForm.dateFormatUS') + ' (02/20/2020)'"
            value="US"
          ></DropdownItem>
          <DropdownItem
            :name="$t('fieldDateSubForm.dateFormatISO') + ' (2020-20-02)'"
            value="ISO"
          ></DropdownItem>
        </Dropdown>
      </div>
    </div>
    <div class="control">
      <div class="control__elements">
        <Checkbox v-model="values.date_include_time">{{
          $t('fieldDateSubForm.includeTimeLabel')
        }}</Checkbox>
      </div>
    </div>
    <div v-show="values.date_include_time" class="control">
      <label class="control__label control__label--small">{{
        $t('fieldDateSubForm.timeFormatLabel')
      }}</label>
      <div class="control__elements">
        <Dropdown
          v-model="values.date_time_format"
          :class="{ 'dropdown--error': $v.values.date_time_format.$error }"
          @hide="$v.values.date_time_format.$touch()"
        >
          <DropdownItem
            :name="$t('fieldDateSubForm.24Hour') + ' (23:00)'"
            value="24"
          ></DropdownItem>
          <DropdownItem
            :name="$t('fieldDateSubForm.12Hour') + ' (11:00 PM)'"
            value="12"
          ></DropdownItem>
        </Dropdown>
      </div>
    </div>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'

export default {
  name: 'FieldDateSubForm',
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['date_format', 'date_include_time', 'date_time_format'],
      values: {
        date_format: 'EU',
        date_include_time: false,
        date_time_format: '24',
      },
    }
  },
  validations: {
    values: {
      date_format: { required },
      date_time_format: { required },
    },
  },
}
</script>

<i18n>
{
  "en": {
    "fieldDateSubForm": {
      "dateFormatLabel": "Date format",
      "dateFormatEuropean": "European",
      "dateFormatUS": "US",
      "dateFormatISO": "ISO",
      "includeTimeLabel": "Include time",
      "timeFormatLabel": "Time format",
      "24Hour": "24 hour",
      "12Hour": "12 hour"
    }
  },
  "fr": {
    "fieldDateSubForm": {
      "dateFormatLabel": "Format de date",
      "dateFormatEuropean": "Européen",
      "dateFormatUS": "Américain",
      "dateFormatISO": "ISO",
      "includeTimeLabel": "Inclure l'heure",
      "timeFormatLabel": "Format de l'heure",
      "24Hour": "24 heures",
      "12Hour": "12 heures"
    }
  }
}
</i18n>
