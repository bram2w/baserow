<template>
  <div class="form-view__submitted">
    <template v-if="isRedirect">
      <div class="form-view__submitted-message">
        Thanks for submitting the form!
      </div>
      <div class="form-view__redirecting-description">
        You're being redirected to {{ submitActionRedirectUrl }}.
      </div>
      <div class="form-view__redirecting-loading">
        <div class="loading-absolute-center"></div>
      </div>
    </template>
    <div v-else class="form-view__submitted-message">
      {{ submitActionMessage || 'Thanks for submitting the form!' }}
    </div>
    <FormViewPoweredBy v-if="showLogo"></FormViewPoweredBy>
  </div>
</template>

<script>
import FormViewPoweredBy from '@baserow/modules/database/components/view/form/FormViewPoweredBy'

export default {
  name: 'FormViewSubmitted',
  components: {
    FormViewPoweredBy,
  },
  props: {
    isRedirect: {
      type: Boolean,
      required: true,
    },
    submitActionRedirectUrl: {
      type: String,
      required: true,
    },
    submitActionMessage: {
      type: String,
      required: true,
    },
    showLogo: {
      type: Boolean,
      required: true,
    },
  },
}
</script>
