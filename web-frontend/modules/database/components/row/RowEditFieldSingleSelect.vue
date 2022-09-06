<template>
  <div class="control__elements">
    <FieldSelectOptionsDropdown
      :value="valueId"
      :options="field.select_options"
      :allow-create-option="allowCreateOptions"
      :disabled="readOnly"
      :class="{ 'dropdown--error': touched && !valid }"
      @input="updateValue($event, value)"
      @create-option="createOption($event)"
      @hide="touch()"
    ></FieldSelectOptionsDropdown>
    <div v-show="touched && !valid" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import singleSelectField from '@baserow/modules/database/mixins/singleSelectField'
import FieldSelectOptionsDropdown from '@baserow/modules/database/components/field/FieldSelectOptionsDropdown'

export default {
  name: 'RowEditFieldSingleSelect',
  components: { FieldSelectOptionsDropdown },
  mixins: [rowEditField, singleSelectField],
  props: {
    allowCreateOptions: {
      type: Boolean,
      default: true,
      required: false,
    },
  },
}
</script>
