<template>
  <FormElement :error="hasErrors" class="control">
    <label class="control__label">
      {{ $t('pageForm.pathTitle') }}
    </label>
    <div class="control__description">
      {{ $t('pageForm.pathSubtitle') }}
    </div>
    <div class="control__elements">
      <input
        :value="value"
        class="input"
        :class="{ 'input--error': hasErrors }"
        type="text"
        @input="$emit('input', $event.target.value)"
        @blur="$emit('blur')"
      />
      <div
        v-if="validationState.$dirty && !validationState.required"
        class="error"
      >
        {{ $t('error.requiredField') }}
      </div>
      <div
        v-if="validationState.$dirty && !validationState.isUnique"
        class="error"
      >
        {{ $t('pageErrors.errorPathNotUnique') }}
      </div>
      <div
        v-if="validationState.$dirty && !validationState.maxLength"
        class="error"
      >
        {{ $t('error.maxLength', { max: 255 }) }}
      </div>
      <div
        v-if="validationState.$dirty && !validationState.startingSlash"
        class="error"
      >
        {{ $t('pageErrors.errorStartingSlash') }}
      </div>
      <div
        v-if="validationState.$dirty && !validationState.validPathCharacters"
        class="error"
      >
        {{ $t('pageErrors.errorValidPathCharacters') }}
      </div>
      <div
        v-if="validationState.$dirty && !validationState.uniquePathParams"
        class="error"
      >
        {{ $t('pageErrors.errorUniquePathParams') }}
      </div>
    </div>
  </FormElement>
</template>

<script>
export default {
  name: 'PageSettingsPathFormElement',
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
  },
}
</script>
