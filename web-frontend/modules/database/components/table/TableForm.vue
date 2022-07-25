<template>
  <form @submit.prevent="submit">
    <FormElement
      v-if="creation"
      :error="fieldHasErrors('name')"
      class="control"
    >
      <label class="control__label">
        <i class="fas fa-font"></i>
        {{ $t('tableForm.name') }}
      </label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': fieldHasErrors('name') }"
          type="text"
          class="input input--large"
          @blur="$v.values.name.$touch()"
        />
        <div v-if="fieldHasErrors('name')" class="error">
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <slot></slot>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'TableForm',
  mixins: [form],
  props: {
    creation: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  data() {
    return {
      values: {
        name: '',
      },
    }
  },
  validations: {
    values: {
      name: {
        // No object-shorthand here to access vm properties
        // eslint-disable-next-line object-shorthand
        required: function (value) {
          if (this.creation) {
            return required(value)
          }
          return true
        },
      },
    },
  },
  mounted() {
    if (this.creation) {
      this.$refs.name.focus()
    }
  },
}
</script>
