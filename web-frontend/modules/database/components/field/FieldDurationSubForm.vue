<template>
  <div>
    <div class="control">
      <label class="control__label control__label--small">{{
        $t('fieldDurationSubForm.durationFormatLabel')
      }}</label>
      <div class="control__elements">
        <Dropdown
          v-model="values.duration_format"
          :class="{ 'dropdown--error': $v.values.duration_format.$error }"
          :fixed-items="true"
          small
          @hide="$v.values.duration_format.$touch()"
        >
          <DropdownItem
            v-for="option in durationFormatOptions"
            :key="option.value"
            :name="option.name"
            :value="option.value"
          ></DropdownItem>
        </Dropdown>
      </div>
    </div>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import { DURATION_FORMATS } from '@baserow/modules/database/utils/duration'

import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'

export default {
  name: 'FieldDurationSubForm',
  mixins: [form, fieldSubForm],
  data() {
    const allowedValues = ['duration_format']
    const values = { duration_format: DURATION_FORMATS.keys().next().value }

    return {
      allowedValues,
      values,
    }
  },
  computed: {
    durationFormatOptions() {
      return Array.from(DURATION_FORMATS.entries()).map(
        ([key, formatOption]) => ({
          name: formatOption.description,
          value: key,
        })
      )
    },
  },
  validations: {
    values: {
      duration_format: { required },
    },
  },
}
</script>
