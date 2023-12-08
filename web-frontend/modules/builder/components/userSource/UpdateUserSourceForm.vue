<template>
  <form>
    <FormRow>
      <FormInput
        v-model="$v.values.name.$model"
        :label="$t('updateUserSourceForm.nameFieldLabel')"
        class="update-user-source-form__name-input"
        :placeholder="$t('updateUserSourceForm.nameFieldPlaceholder')"
        :error="getError('name')"
      />
      <FormGroup
        :label="$t('updateUserSourceForm.integrationFieldLabel')"
        :error="getError('integration_id')"
      >
        <IntegrationDropdown
          v-model="$v.values.integration_id.$model"
          :application="builder"
          :integrations="integrations"
          :integration-type="userSourceType.integrationType"
        />
      </FormGroup>
    </FormRow>
    <component
      :is="userSourceType.formComponent"
      v-if="integration"
      :default-values="defaultValues"
      :application="builder"
      :integration="integration"
    />
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import IntegrationDropdown from '@baserow/modules/core/components/integrations/IntegrationDropdown'
import { required, maxLength } from 'vuelidate/lib/validators'

export default {
  components: { IntegrationDropdown },
  mixins: [form],
  props: {
    builder: {
      type: Object,
      required: true,
    },
    userSourceType: {
      type: Object,
      required: false,
      default: null,
    },
    integrations: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      values: {
        integration_id: null,
        name: '',
      },
      allowedValues: ['integration_id', 'name'],
    }
  },
  computed: {
    integration() {
      if (!this.values.integration_id) {
        return null
      }
      return this.integrations.find(
        ({ id }) => id === this.values.integration_id
      )
    },
  },
  methods: {
    getError(fieldName) {
      if (!this.$v.values[fieldName].$dirty) {
        return ''
      }
      const fieldState = this.$v.values[fieldName]
      if (!fieldState.required) {
        return this.$t('error.requiredField')
      }
      if (fieldName === 'name' && !fieldState.maxLength) {
        return this.$t('error.maxLength', { max: 255 })
      }
      return ''
    },
  },
  validations: {
    values: {
      integration_id: {
        required,
      },
      name: {
        required,
        maxLength: maxLength(255),
      },
    },
  },
}
</script>
