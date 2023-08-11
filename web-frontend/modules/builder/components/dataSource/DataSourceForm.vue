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
          class="data-source-form__type-dropdown"
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
        <Dropdown
          v-model="values.integration_id"
          class="data-source-form__integration-dropdown"
          :disabled="!values.type"
          :placeholder="
            !serviceType
              ? $t('dataSourceForm.selectTypeFirst')
              : $t('dataSourceForm.integrationPlaceholder')
          "
          show-footer
        >
          <DropdownItem
            v-for="integration in integrations"
            :key="integration.id"
            :name="integration.name"
            :value="integration.id"
          />
          <template #emptyState>
            {{ $t('dataSourceForm.noIntegrations') }}
          </template>
          <template #footer>
            <a
              class="select__footer-button"
              @click="$refs.IntegrationCreateEditModal.show()"
            >
              <i class="fas fa-plus"></i>
              {{ $t('dataSourceForm.addIntegration') }}
            </a>
            <IntegrationCreateEditModal
              v-if="serviceType"
              ref="IntegrationCreateEditModal"
              :application="builder"
              :integration-type="serviceType.integrationType"
              create
              @created="values.integration_id = $event.id"
            />
          </template>
        </Dropdown>
        <Button icon="trash" type="light" @click="$emit('delete')" />
      </div>
      <div v-if="headerError" class="error">
        {{ headerError }}
      </div>
    </div>
    <template v-if="serviceType">
      <component
        :is="serviceType.formComponent"
        ref="subForm"
        :builder="builder"
        :default-values="defaultValues"
        @values-changed="emitChange($event)"
      />
    </template>
  </div>
</template>

<script>
import IntegrationCreateEditModal from '@baserow/modules/core/components/integrations/IntegrationCreateEditModal'
import form from '@baserow/modules/core/mixins/form'
import { required, maxLength } from 'vuelidate/lib/validators'

export default {
  name: 'DataSourceContext',
  components: { IntegrationCreateEditModal },
  mixins: [form],
  props: {
    builder: {
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
  },
  data() {
    return {
      allowedValues: ['name', 'integration_id', 'type'],
      values: { name: '', integration_id: undefined, type: '' },
    }
  },
  computed: {
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
