<template>
  <FormGroup :error="touched && !valid">
    <FormTextarea
      ref="input"
      v-model="copy"
      :error="touched && !valid"
      :disabled="readOnly"
      :rows="5"
      @focus="select()"
      @blur="unselect()"
    />

    <template #error>
      {{ error }}
    </template>
  </FormGroup>
</template>

<script>
import FormTextarea from '@baserow/modules/core/components/FormTextarea.vue'
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import rowEditFieldInput from '@baserow/modules/database/mixins/rowEditFieldInput'

export default {
  components: { FormTextarea },
  mixins: [rowEditField, rowEditFieldInput],
}
</script>
