<template>
  <form @submit.prevent>
    <FormElement class="control">
      <label class="control__label">{{ label }}</label>
      <div class="control__elements">
        <div>
          <input
            v-model="values.padding"
            type="number"
            class="input"
            :class="{
              'input--error': error,
            }"
            @blur="$v.values.padding.$touch()"
          />
        </div>
        <div v-if="error" class="error">
          {{ error }}
        </div>
      </div>
    </FormElement>
  </form>
</template>

<script>
import { required, integer, between } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'

export default {
  mixins: [form],
  props: {
    label: {
      type: String,
      required: true,
    },
    value: {
      type: Object,
      required: true,
    },
  },
  data() {
    return { values: { padding: 0 } }
  },
  computed: {
    /**
     * Returns only one error because we don't have the space to write one error per
     * field as the style fields are on the same line.
     */
    error() {
      if (this.$v.values.padding.$error) {
        return this.$t('styleBoxForm.paddingError')
      } else {
        return ''
      }
    },
  },
  methods: {
    getDefaultValues() {
      return this.value
    },
    emitChange(newValues) {
      this.$emit('input', newValues)
    },
  },
  validations() {
    return {
      values: {
        padding: {
          required,
          integer,
          between: between(0, 200),
        },
      },
    }
  },
}
</script>
