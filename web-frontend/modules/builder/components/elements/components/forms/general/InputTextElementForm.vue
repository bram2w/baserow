<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormInput
      v-model="values.default_value"
      :label="$t('inputTextElementForm.valueTitle')"
      :placeholder="$t('inputTextElementForm.valuePlaceholder')"
    />
    <FormInput
      v-model="values.placeholder"
      :label="$t('inputTextElementForm.placeholderTitle')"
      :error="
        $v.values.placeholder.$dirty && !$v.values.placeholder.maxLength
          ? $t('error.maxLength', { max: 255 })
          : ''
      "
      :placeholder="$t('inputTextElementForm.placeholderPlaceholder')"
      @blur="$v.values.placeholder.$touch()"
    />
    <FormElement class="control">
      <label class="control__label">
        {{ $t('inputTextElementForm.requiredTitle') }}
      </label>
      <div class="control__elements">
        <Checkbox v-model="values.required"></Checkbox>
      </div>
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { maxLength } from 'vuelidate/lib/validators'

export default {
  name: 'InputTextElementForm',
  mixins: [form],
  props: {},
  data() {
    return {
      values: {
        default_value: '',
        required: false,
        placeholder: '',
      },
    }
  },
  methods: {
    emitChange(newValues) {
      if (this.isFormValid()) {
        form.methods.emitChange.bind(this)(newValues)
      }
    },
  },
  validations() {
    return {
      values: {
        placeholder: {
          maxLength: maxLength(225),
        },
      },
    }
  },
}
</script>
