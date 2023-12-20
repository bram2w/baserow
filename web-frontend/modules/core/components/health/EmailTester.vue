<template>
  <div>
    <h2>
      {{ $t('emailTester.title') }}

      <a
        href="https://baserow.io/docs/installation%2Fconfiguration#email-configuration"
        target="_blank"
        ><i class="iconoir-chat-bubble-question"
      /></a>
    </h2>
    <Error :error="error" />
    <div v-if="testResult.succeeded != null">
      <Alert v-if="!testResult.succeeded" type="error">
        <template #title>{{ testResult.error_type }}</template>
        <div>
          <p>{{ testResult.error }}</p>
          <pre class="email-tester__full-stack">{{ trimmedFullStack }}</pre>
        </div>
      </Alert>
      <Alert v-else type="success">
        <template #title>{{ $t('emailTester.success') }}</template>
      </Alert>
    </div>
    <form @submit.prevent="submit">
      <FormElement :error="fieldHasErrors('targetEmail')" class="control">
        <label class="control__label">{{
          $t('emailTester.targetEmailLabel')
        }}</label>
        <div class="control__elements">
          <input
            ref="name"
            v-model="values.targetEmail"
            :class="{ 'input--error': fieldHasErrors('targetEmail') }"
            type="text"
            class="input"
            :disabled="loading"
            @blur="$v.values.targetEmail.$touch()"
          />
          <div v-if="fieldHasErrors('targetEmail')" class="error">
            {{ $t('emailTester.invalidTargetEmail') }}
          </div>
        </div>
      </FormElement>
      <button
        class="button button--primary"
        :class="{ 'button--loading': loading }"
        :disabled="loading || $v.$invalid"
      >
        {{ $t('emailTester.submit') }}
      </button>
    </form>
  </div>
</template>

<script>
import error from '@baserow/modules/core/mixins/error'
import HealthService from '@baserow/modules/core/services/health'
import form from '@baserow/modules/core/mixins/form'

import { required, email } from 'vuelidate/lib/validators'
import { mapGetters } from 'vuex'
export default {
  name: 'EmailerTester',
  mixins: [error, form],
  data() {
    return {
      loading: false,
      values: {
        targetEmail: 'test@example.com',
      },
      testResult: {
        succeeded: null,
        error_type: null,
        error: null,
        error_stack: null,
      },
    }
  },
  computed: {
    ...mapGetters({ username: 'auth/getUsername' }),
    trimmedFullStack() {
      return this.testResult?.error_stack?.trim()
    },
  },
  mounted() {
    if (this.username) {
      this.values.targetEmail = this.username
    }
  },
  methods: {
    async submit() {
      this.loading = true
      this.testResult = {}
      this.hideError()

      try {
        const { data } = await HealthService(this.$client).testEmail(
          this.values.targetEmail
        )
        this.testResult = data
      } catch (e) {
        this.handleError(e, 'health')
        this.testResult = {}
      }

      this.loading = false
    },
  },
  validations: {
    values: {
      targetEmail: { required, email },
    },
  },
}
</script>
