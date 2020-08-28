<template>
  <div>
    <div class="control">
      <label class="control__label control__label--small">Date format</label>
      <div class="control__elements">
        <Dropdown
          v-model="values.date_format"
          :class="{ 'dropdown--error': $v.values.date_format.$error }"
          @hide="$v.values.date_format.$touch()"
        >
          <DropdownItem name="European (20/02/2020)" value="EU"></DropdownItem>
          <DropdownItem name="US (02/20/2020)" value="US"></DropdownItem>
          <DropdownItem name="ISO (2020-20-02)" value="ISO"></DropdownItem>
        </Dropdown>
      </div>
    </div>
    <div class="control">
      <div class="control__elements">
        <Checkbox v-model="values.date_include_time">Include time</Checkbox>
      </div>
    </div>
    <div v-show="values.date_include_time" class="control">
      <label class="control__label control__label--small">Time format</label>
      <div class="control__elements">
        <Dropdown
          v-model="values.date_time_format"
          :class="{ 'dropdown--error': $v.values.date_time_format.$error }"
          @hide="$v.values.date_time_format.$touch()"
        >
          <DropdownItem name="24 hour (23:00)" value="24"></DropdownItem>
          <DropdownItem name="12 hour (11:00 PM)" value="12"></DropdownItem>
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
