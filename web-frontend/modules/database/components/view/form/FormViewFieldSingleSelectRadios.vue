<template>
  <div class="control__elements">
    <div v-for="option in field.select_options" :key="option.id">
      <Radio
        :model-value="valueId"
        :value="option.id"
        @input=";[touch(), updateValue($event, value)]"
        >{{ option.value }}</Radio
      >
    </div>
    <div v-if="!required" class="margin-top-1">
      <a @click=";[touch(), updateValue(null, value)]">clear value</a>
    </div>
    <div v-show="touched && !valid" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import singleSelectField from '@baserow/modules/database/mixins/singleSelectField'

export default {
  name: 'FormViewSingleSelectRadios',
  mixins: [rowEditField, singleSelectField],
}
</script>
