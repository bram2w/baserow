<template>
  <form @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('name')" class="control">
      <label class="control__label">{{
        $t('oauthSettingsForm.providerName')
      }}</label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': fieldHasErrors('name') }"
          type="text"
          class="input"
          :placeholder="$t('oauthSettingsForm.providerNamePlaceholder')"
          @blur="$v.values.name.$touch()"
        />
        <div
          v-if="$v.values.name.$dirty && !$v.values.name.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <FormElement :error="fieldHasErrors('base_url')" class="control">
      <label class="control__label">{{
        $t('oauthSettingsForm.baseUrl')
      }}</label>
      <div class="control__elements">
        <input
          ref="base_url"
          v-model="values.base_url"
          :class="{ 'input--error': fieldHasErrors('base_url') }"
          type="text"
          class="input"
          :placeholder="$t('oauthSettingsForm.baseUrlPlaceholder')"
          @blur="$v.values.base_url.$touch()"
        />
        <div
          v-if="$v.values.base_url.$dirty && !$v.values.base_url.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
        <div
          v-if="$v.values.base_url.$dirty && !$v.values.base_url.url"
          class="error"
        >
          {{ $t('oauthSettingsForm.invalidBaseUrl') }}
        </div>
      </div>
    </FormElement>
    <FormElement :error="fieldHasErrors('client_id')" class="control">
      <label class="control__label">{{
        $t('oauthSettingsForm.clientId')
      }}</label>
      <div class="control__elements">
        <input
          ref="client_id"
          v-model="values.client_id"
          :class="{ 'input--error': fieldHasErrors('client_id') }"
          type="text"
          class="input"
          :placeholder="$t('oauthSettingsForm.clientIdPlaceholder')"
          @blur="$v.values.client_id.$touch()"
        />
        <div
          v-if="$v.values.client_id.$dirty && !$v.values.client_id.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <FormElement :error="fieldHasErrors('secret')" class="control">
      <label class="control__label">{{ $t('oauthSettingsForm.secret') }}</label>
      <div class="control__elements">
        <input
          ref="secret"
          v-model="values.secret"
          :class="{ 'input--error': fieldHasErrors('secret') }"
          type="text"
          class="input"
          :placeholder="$t('oauthSettingsForm.secretPlaceholder')"
          @blur="$v.values.secret.$touch()"
        />
        <div
          v-if="$v.values.secret.$dirty && !$v.values.secret.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <div class="control">
      <label class="control__label">{{
        $t('oauthSettingsForm.callbackUrl')
      }}</label>
      <div class="control__elements">
        <code>{{ callbackUrl }}</code>
      </div>
    </div>
    <slot></slot>
  </form>
</template>

<script>
import { required, url } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'GitLabSettingsForm',
  mixins: [form],
  props: {
    authProvider: {
      type: Object,
      required: false,
      default: () => ({}),
    },
  },
  data() {
    return {
      allowedValues: ['name', 'base_url', 'client_id', 'secret'],
      values: {
        name: '',
        base_url: '',
        client_id: '',
        secret: '',
      },
    }
  },
  computed: {
    providerName() {
      return this.$registry
        .get('authProvider', 'gitlab')
        .getProviderName(this.authProvider)
    },
    callbackUrl() {
      if (!this.authProvider.id) {
        const nextProviderId =
          this.$store.getters['authProviderAdmin/getNextProviderId']
        return `${this.$env.PUBLIC_BACKEND_URL}/api/sso/oauth2/callback/${nextProviderId}/`
      }
      return `${this.$env.PUBLIC_BACKEND_URL}/api/sso/oauth2/callback/${this.authProvider.id}/`
    },
  },
  methods: {
    getDefaultValues() {
      return {
        name: this.providerName,
        base_url: this.authProvider.base_url || 'https://gitlab.com',
        client_id: this.authProvider.client_id || '',
        secret: this.authProvider.secret || '',
      }
    },
    submit() {
      this.$v.$touch()
      if (this.$v.$invalid) {
        return
      }
      this.$emit('submit', this.values)
    },
  },
  validations() {
    return {
      values: {
        name: { required },
        base_url: { url, required },
        client_id: { required },
        secret: { required },
      },
    }
  },
}
</script>
