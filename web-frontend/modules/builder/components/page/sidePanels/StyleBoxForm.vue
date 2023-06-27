<template>
  <form @submit.prevent>
    <FormElement class="control">
      <label class="control__label">{{ label }}</label>
      <div class="control__elements">
        <input
          v-model="values[paddingName]"
          type="number"
          class="input"
          :class="{ 'input--error': $v.values[paddingName].$error }"
          @blur="$v.values[paddingName].$touch()"
        />
        <div v-if="$v.values[paddingName].$error" class="error">
          {{ $t('styleBoxForm.paddingError') }}
        </div>
      </div>
    </FormElement>
  </form>
</template>

<script>
import { required, integer, between } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'StyleBoxForm',
  mixins: [form],
  props: {
    label: {
      type: String,
      required: true,
    },
    paddingName: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: [this.paddingName],
      values: {
        [this.paddingName]: 0,
      },
    }
  },
  validations() {
    return {
      values: {
        [this.paddingName]: {
          required,
          integer,
          between: between(0, 200),
        },
      },
    }
  },
  methods: {
    emitChange(newValues) {
      if (this.isFormValid()) {
        this.$emit('values-changed', newValues)
      }
    },
  },
}
</script>
