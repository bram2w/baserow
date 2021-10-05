<!--
This helper component can only be used in a form which uses the password validation
from modules/core/validators.js
as ist expects the following vuelidate validation state params

- required
- maxLength
- minLength

In order to use this component in another component/form it needs a value
prop which can be passed via the 'v-model' directive. That means the state for the 
password value always lives in the parent component.
The parent component also needs to provide the vuelidate password validation in order
for this component to show all the possible validation errors.

Example Usage:

<PasswordInput
   v-model="PASSWORDSTATE"
   :validation-state="the vuelidate validation instance of the given password value"
/>

In case the password validation rules change, the passwordValidation object in the
validators file needs to be updated, as well as this component.

modules/core/validators.js

-->
<template>
  <div>
    <input
      :class="{ 'input--error': validationState.$error }"
      type="password"
      class="input input--large"
      :value="value"
      @blur="validationState.$touch()"
      @input="$emit('input', $event.target.value)"
    />
    <div
      v-if="validationState.$error && !validationState.required"
      class="error"
    >
      {{ $t('error.inputRequired') }}
    </div>
    <div
      v-if="validationState.$error && !validationState.maxLength"
      class="error"
    >
      {{
        $t('error.maxLength', {
          max: validationState.$params.maxLength.max,
        })
      }}
    </div>
    <div
      v-if="validationState.$error && !validationState.minLength"
      class="error"
    >
      {{
        $t('error.minLength', {
          min: validationState.$params.minLength.min,
        })
      }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'PasswordInput',
  props: {
    validationState: {
      type: Object,
      required: true,
    },
    value: {
      type: String,
      required: true,
    },
  },
}
</script>

<i18n>
{
  "en":{
    "error":{
      "inputRequired": "Input is required."

    }
  },
  "fr": {
    "error":{
      "inputRequired": "Ce champ est obligatoire."
    }
  }
}
</i18n>
