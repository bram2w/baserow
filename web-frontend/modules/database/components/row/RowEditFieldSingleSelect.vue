<template>
  <div class="control__elements">
    <FieldSelectOptionsDropdown
      :value="valueId"
      :options="field.select_options"
      :allow-create-option="true"
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
import selectOptions from '@baserow/modules/database/mixins/selectOptions'
import singleSelectField from '@baserow/modules/database/mixins/singleSelectField'

export default {
  name: 'RowEditFieldSingleSelect',
  mixins: [rowEditField, selectOptions, singleSelectField],
}
</script>
