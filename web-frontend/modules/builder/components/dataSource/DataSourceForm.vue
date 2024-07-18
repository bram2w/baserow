<template>
  <div class="data-source-form">
    <div class="data-source-form__header">
      <div class="data-source-form__header-form">
        <FormInput
          v-model="values.name"
          class="data-source-form__name-input"
          :placeholder="$t('dataSourceForm.namePlaceholder')"
        />
        <Dropdown
          v-model="values.type"
          fixed-items
          class="dropdown--small data-source-form__type-dropdown"
          :placeholder="$t('dataSourceForm.servicePlaceholder')"
        >
          <template
            v-for="[, serviceTypesForDrop] in serviceTypesPerIntegration"
          >
            <DropdownItem
              v-for="serviceTypeForDrop in serviceTypesForDrop"
              :key="serviceTypeForDrop.getType()"
              :name="serviceTypeForDrop.name"
              :value="serviceTypeForDrop.getType()"
              :image="serviceTypeForDrop.integrationType.image"
            >
            </DropdownItem>
          </template>
        </Dropdown>
        <IntegrationDropdown
          v-model="values.integration_id"
          class="data-source-form__integration-dropdown"
          :application="builder"
          :integrations="integrations"
          :disabled="!values.type"
          :integration-type="serviceType?.integrationType"
          small
        />
        <ButtonIcon icon="iconoir-bin" @click="$emit('delete')" />
      </div>
      <div v-if="headerError" class="error">
        {{ headerError }}
      </div>
    </div>
    <div v-if="loading" class="loading margin-bottom-1"></div>
    <template v-if="serviceType && integration && !loading">
      <component
        :is="serviceType.formComponent"
        ref="subForm"
        :builder="builder"
        :data-source="dataSource"
        :default-values="defaultValues"
        :context-data="integration.context_data"
        @values-changed="emitChange($event)"
      />
    </template>
  </div>
</template>

<script>
import IntegrationDropdown from '@baserow/modules/core/components/integrations/IntegrationDropdown'
import form from '@baserow/modules/core/mixins/form'
import { required, maxLength } from 'vuelidate/lib/validators'
import { DATA_PROVIDERS_ALLOWED_DATA_SOURCES } from '@baserow/modules/builder/enums'

export default {
  name: 'DataSourceContext',
  components: { IntegrationDropdown },
  mixins: [form],
  provide() {
    return { dataProvidersAllowed: DATA_PROVIDERS_ALLOWED_DATA_SOURCES }
  },
  props: {
    builder: {
      type: Object,
      required: true,
    },
    dataSource: {
      type: Object,
      required: true,
    },
    page: {
      type: Object,
      required: true,
    },
    integrations: {
      type: Array,
      required: true,
    },
    id: {
      type: Number,
      required: true,
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      allowedValues: ['name', 'integration_id', 'type'],
      values: { name: '', integration_id: undefined, type: '' },
    }
  },
  computed: {
    integration() {
      return this.integrations.find(
        (integration) => integration.id === this.values.integration_id
      )
    },
    serviceTypes() {
      return this.$registry.getOrderedList('service')
    },
    serviceType() {
      return this.values.type
        ? this.$registry.get('service', this.values.type)
        : null
    },
    serviceTypesPerIntegration() {
      return this.$registry
        .getOrderedList('integration')
        .map((integrationType) => [
          integrationType,
          this.serviceTypes.filter(
            (serviceType) => serviceType.integrationType === integrationType
          ),
        ])
    },
    headerError() {
      return !this.$v.values.name.required
        ? this.$t('error.requiredField')
        : !this.$v.values.name.maxLength
        ? this.$t('error.maxLength', { max: 255 })
        : !this.$v.values.name.unique
        ? this.$t('dataSourceForm.errorUniqueName')
        : ''
    },
  },
  methods: {
    emitChange(newValues) {
      if (
        this.isFormValid() &&
        (!this.$refs.subForm || this.$refs.subForm.isFormValid())
      ) {
        this.$emit('values-changed', newValues)
      }
    },
    mustHaveUniqueName(param) {
      const existingNames = this.$store.getters[
        'dataSource/getPageDataSources'
      ](this.page)
        .filter(({ id }) => id !== this.defaultValues.id)
        .map(({ name }) => name)
      return !existingNames.includes(param.trim())
    },
  },
  validations() {
    return {
      values: {
        name: {
          required,
          maxLength: maxLength(255),
          unique: this.mustHaveUniqueName,
        },
      },
    }
  },
}
</script>
