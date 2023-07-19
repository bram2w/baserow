<template>
  <FormElement :error="hasErrors" class="control">
    <label class="control__label">
      {{ $t('pageForm.nameTitle') }}
    </label>
    <div class="control__description">
      {{ $t('pageForm.nameSubtitle') }}
    </div>
    <div class="control__elements">
      <input
        ref="input"
        :value="value"
        class="input"
        :class="{ 'input--error': hasErrors }"
        type="text"
        @input="$emit('input', $event.target.value)"
        @blur="$emit('blur')"
        @focus.once="isCreation && $event.target.select()"
      />
      <div
        v-if="validationState.$dirty && !validationState.required"
        class="error"
      >
        {{ $t('error.requiredField') }}
      </div>
      <div
        v-if="validationState.$dirty && !validationState.maxLength"
        class="error"
      >
        {{ $t('error.maxLength', { max: 255 }) }}
      </div>
      <div
        v-if="validationState.$dirty && !validationState.isUnique"
        class="error"
      >
        {{ $t('pageErrors.errorNameNotUnique') }}
      </div>
    </div>
  </FormElement>
</template>

<script>
export default {
  name: 'PageSettingsNameFormElement',
  props: {
    value: {
      type: String,
      required: false,
      default: '',
    },
    hasErrors: {
      type: Boolean,
      required: false,
      default: false,
    },
    validationState: {
      type: Object,
      required: false,
      default: () => {},
    },
    isCreation: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
}
</script>
