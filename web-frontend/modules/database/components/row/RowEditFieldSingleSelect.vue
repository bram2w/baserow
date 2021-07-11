<template>
  <div class="control__elements">
    <FieldSingleSelectDropdown
      :value="valueId"
      :options="field.select_options"
      :allow-create-option="true"
      :disabled="readOnly"
      :class="{ 'dropdown--error': touched && !valid }"
      @input="updateValue($event, value)"
      @create-option="createOption($event)"
      @hide="touch()"
    ></FieldSingleSelectDropdown>
    <div v-show="touched && !valid" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import singleSelectField from '@baserow/modules/database/mixins/singleSelectField'

export default {
  name: 'RowEditFieldSingleSelectVue',
  mixins: [rowEditField, singleSelectField],
  methods: {
    updateValue(...args) {
      singleSelectField.methods.updateValue.call(this, ...args)
    },
  },
}
</script>
