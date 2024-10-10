<template>
  <form @submit.prevent="submit">
    <FormGroup :error="fieldHasErrors('name')" small-label required>
      <slot name="settings"> </slot>

      <template #after-input>
        <slot></slot>
      </template>
    </FormGroup>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { required } from 'vuelidate/lib/validators'

export default {
  name: 'ExportWorkspaceForm',
  mixins: [form],
  data() {
    return {
      values: {
        only_structure: false,
        application_ids: [],
      },
    }
  },
  validations() {
    return {
      values: {
        only_structure: {
          required,
        },
      },
    }
  },
}
</script>
