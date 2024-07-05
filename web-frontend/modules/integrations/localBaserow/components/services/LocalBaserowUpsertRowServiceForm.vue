<template>
  <form @submit.prevent>
    <FormGroup
      :label="$t('upsertRowWorkflowActionForm.integrationDropdownLabel')"
      small-label
      required
    >
      <IntegrationDropdown
        v-model="values.integration_id"
        :application="application"
        :integrations="integrations"
        :integration-type="integrationType"
      />
    </FormGroup>
    <LocalBaserowTableSelector
      v-if="selectedIntegration"
      v-model="fakeTableId"
      :databases="databases"
      :display-view-dropdown="false"
      class="margin-top-2"
    ></LocalBaserowTableSelector>

    <InjectedFormulaInputGroup
      v-if="enableRowId && values.integration_id"
      v-model="values.row_id"
      small
      small-label
      :placeholder="$t('upsertRowWorkflowActionForm.rowIdPlaceholder')"
      :label="$t('upsertRowWorkflowActionForm.rowIdLabel')"
    />
    <p v-if="selectedIntegration && !values.table_id">
      {{ $t('upsertRowWorkflowActionForm.noTableSelectedMessage') }}
    </p>
    <div v-if="tableLoading" class="loading margin-bottom-1"></div>
    <FieldMappingForm
      v-if="!tableLoading"
      v-model="values.field_mappings"
      :fields="getWritableSchemaFields"
    ></FieldMappingForm>
  </form>
</template>

<script>
import LocalBaserowTableSelector from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowTableSelector'
import { LocalBaserowIntegrationType } from '@baserow/modules/integrations/integrationTypes'
import FieldMappingForm from '@baserow/modules/integrations/localBaserow/components/services/FieldMappingForm'
import InjectedFormulaInputGroup from '@baserow/modules/core/components/formula/InjectedFormulaInputGroup'
import IntegrationDropdown from '@baserow/modules/core/components/integrations/IntegrationDropdown'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'LocalBaserowUpsertRowServiceForm',
  components: {
    IntegrationDropdown,
    FieldMappingForm,
    LocalBaserowTableSelector,
    InjectedFormulaInputGroup,
  },
  mixins: [form],
  props: {
    application: {
      type: Object,
      required: true,
    },
    workflowAction: {
      type: Object,
      required: false,
      default: null,
    },
    enableRowId: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      allowedValues: ['row_id', 'table_id', 'integration_id', 'field_mappings'],
      values: {
        row_id: '',
        table_id: null,
        field_mappings: [],
        integration_id: null,
      },
      state: null,
      tableLoading: false,
    }
  },

  computed: {
    integrations() {
      return this.$store.getters['integration/getIntegrations'](
        this.application
      )
    },
    workflowActionLoading() {
      return this.$store.getters['workflowAction/getLoading'](
        this.workflowAction
      )
    },
    fakeTableId: {
      get() {
        return this.values.table_id
      },
      set(newValue) {
        // If we currently have a `table_id` selected, and the `newValue`
        // is different to the current `table_id`, then reset the
        // `field_mappings` to a blank array.
        if (this.values.table_id !== newValue) {
          this.tableLoading = true
          if (this.values.table_id) {
            this.values.field_mappings = []
          }
        }
        this.values.table_id = newValue
      },
    },
    integrationType() {
      return this.$registry.get(
        'integration',
        LocalBaserowIntegrationType.getType()
      )
    },
    selectedIntegration() {
      return this.$store.getters['integration/getIntegrationById'](
        this.application,
        this.values.integration_id
      )
    },
    databases() {
      return this.selectedIntegration?.context_data.databases || []
    },
    getWritableSchemaFields() {
      if (
        this.workflowAction.service == null ||
        this.workflowAction.service.schema == null // have service, no table
      ) {
        return []
      }
      const schema = this.workflowAction.service.schema
      const schemaProperties =
        schema.type === 'array' ? schema.items.properties : schema.properties
      return Object.values(schemaProperties)
        .filter(({ metadata }) => metadata && !metadata.read_only)
        .map((prop) => prop.metadata)
    },
  },
  watch: {
    workflowActionLoading: {
      handler(value) {
        if (!value) {
          this.tableLoading = false
        }
      },
    },
  },
}
</script>
