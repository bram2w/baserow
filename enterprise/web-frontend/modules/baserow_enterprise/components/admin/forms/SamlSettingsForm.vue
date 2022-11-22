<template>
  <form @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('domain')" class="control">
      <label class="control__label"
        >{{ $t('samlSettingsForm.domain') }}
        <img
          v-if="authProvider && authProvider.is_verified"
          class="control__label-right-icon"
          :alt="$t('samlSettingsForm.providerIsVerified')"
          :title="$t('samlSettingsForm.providerIsVerified')"
          :src="getVerifiedIcon()"
        />
      </label>
      <div class="control__elements">
        <input
          ref="domain"
          v-model="values.domain"
          :class="{
            'input--error': fieldHasErrors('domain') || serverErrors.domain,
          }"
          type="text"
          class="input"
          :placeholder="$t('samlSettingsForm.domainPlaceholder')"
          @input="serverErrors.domain = null"
          @blur="$v.values.domain.$touch()"
        />
        <div
          v-if="$v.values.domain.$dirty && !$v.values.domain.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
        <div
          v-else-if="
            $v.values.domain.$dirty && !$v.values.domain.mustHaveUniqueDomain
          "
          class="error"
        >
          {{ $t('samlSettingsForm.domainAlreadyExists') }}
        </div>
        <div v-else-if="serverErrors.domain" class="error">
          {{ $t('samlSettingsForm.invalidDomain') }}
        </div>
      </div>
    </FormElement>
    <FormElement :error="fieldHasErrors('metadata')" class="control">
      <label class="control__label">
        {{ $t('samlSettingsForm.metadata') }}
      </label>
      <div class="control__elements">
        <textarea
          ref="metadata"
          v-model="values.metadata"
          rows="12"
          :class="{
            'input--error': fieldHasErrors('metadata') || serverErrors.metadata,
          }"
          type="textarea"
          class="input saml-settings__metadata"
          :placeholder="$t('samlSettingsForm.metadataPlaceholder')"
          @input="serverErrors.metadata = null"
          @blur="$v.values.metadata.$touch()"
        ></textarea>
        <div
          v-if="$v.values.metadata.$dirty && !$v.values.metadata.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
        <div v-else-if="serverErrors.metadata" class="error">
          {{ $t('samlSettingsForm.invalidMetadata') }}
        </div>
      </div>
    </FormElement>
    <div class="control">
      <label class="control__label">{{
        $t('samlSettingsForm.relayStateUrl')
      }}</label>
      <div class="control__elements">
        <code>{{ getRelayStateUrl() }}</code>
      </div>
    </div>
    <div class="control">
      <label class="control__label">{{ $t('samlSettingsForm.acsUrl') }}</label>
      <div class="control__elements">
        <code>{{ getAcsUrl() }}</code>
      </div>
    </div>
    <slot></slot>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'SamlSettingsForm',
  mixins: [form],
  props: {
    authProvider: {
      type: Object,
      required: false,
      default: () => ({}),
    },
    authProviderType: {
      type: String,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      allowedValues: ['domain', 'metadata'],
      serverErrors: {},
      values: {
        domain: '',
        metadata: '',
      },
    }
  },
  computed: {
    samlDomains() {
      const samlAuthProviders =
        this.$store.getters['authProviderAdmin/getAll'].saml?.authProviders ||
        []
      return samlAuthProviders
        .filter(
          (authProvider) => authProvider.domain !== this.authProvider.domain
        )
        .map((authProvider) => authProvider.domain)
    },
    type() {
      return this.authProviderType || this.authProvider.type
    },
  },
  methods: {
    getDefaultValues() {
      return {
        domain: this.authProvider.domain || '',
        metadata: this.authProvider.metadata || '',
      }
    },
    getRelayStateUrl() {
      return this.$store.getters['authProviderAdmin/getType'](this.type)
        .relayStateUrl
    },
    getAcsUrl() {
      return this.$store.getters['authProviderAdmin/getType'](this.type).acsUrl
    },
    getVerifiedIcon() {
      return this.$registry.get('authProvider', this.type).getVerifiedIcon()
    },
    submit() {
      this.$v.$touch()
      if (this.$v.$invalid) {
        return
      }
      this.$emit('submit', this.values)
    },
    mustHaveUniqueDomain(domain) {
      return !this.samlDomains.includes(domain.trim())
    },
    handleServerError(error) {
      if (error.handler.code !== 'ERROR_REQUEST_BODY_VALIDATION') return false

      for (const [key, value] of Object.entries(error.handler.detail || {})) {
        this.serverErrors[key] = value
      }
      return true
    },
  },
  validations() {
    return {
      values: {
        domain: { required, mustHaveUniqueDomain: this.mustHaveUniqueDomain },
        metadata: { required },
      },
    }
  },
}
</script>
