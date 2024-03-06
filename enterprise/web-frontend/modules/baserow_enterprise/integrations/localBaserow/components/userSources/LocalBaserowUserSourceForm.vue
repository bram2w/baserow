<template>
  <form>
    <LocalBaserowTableSelector
      v-model="computedTableId"
      class="local-baserow-user-source-form__table-selector"
      :databases="integration.context_data.databases"
      :display-view-dropdown="false"
    />

    <p>{{ $t('localBaserowUserSourceForm.description') }}</p>
    <FormRow>
      <FormGroup
        :label="$t('localBaserowUserSourceForm.emailFieldLabel')"
        small-label
      >
        <Dropdown
          v-model="values.email_field_id"
          fixed-items
          :disabled="!selectedTable"
          :placeholder="
            $t('localBaserowUserSourceForm.emailFieldLabelPlaceholder')
          "
        >
          <DropdownItem
            v-for="field in emailFields"
            :key="field.id"
            :name="field.name"
            :value="field.id"
            :icon="getIconForType(field.type)"
          />
          <template #emptyState>
            {{ $t('localBaserowUserSourceForm.noFields') }}
          </template>
        </Dropdown>
      </FormGroup>

      <FormGroup
        :label="$t('localBaserowUserSourceForm.nameFieldLabel')"
        small-label
      >
        <Dropdown
          v-model="values.name_field_id"
          fixed-items
          :disabled="!selectedTable"
          :placeholder="$t('localBaserowUserSourceForm.nameFieldPlaceholder')"
        >
          <DropdownItem
            v-for="field in nameFields"
            :key="field.id"
            :name="field.name"
            :value="field.id"
            :icon="getIconForType(field.type)"
          />
          <template #emptyState>
            {{ $t('localBaserowUserSourceForm.noFields') }}
          </template>
        </Dropdown>
      </FormGroup>
    </FormRow>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import LocalBaserowTableSelector from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowTableSelector'

export default {
  components: {
    LocalBaserowTableSelector,
  },
  mixins: [form],
  props: {
    application: {
      type: Object,
      required: true,
    },
    integration: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      values: {
        table_id: null,
        email_field_id: null,
        name_field_id: null,
      },
      allowedValues: ['table_id', 'email_field_id', 'name_field_id'],
    }
  },
  computed: {
    userSourceType() {
      return this.$registry.get('userSource', 'local_baserow')
    },
    databases() {
      return this.integration.context_data.databases
    },
    fieldTypes() {
      return this.$registry.getAll('field')
    },
    computedTableId: {
      get() {
        return this.values.table_id
      },
      set(newValue) {
        // If we currently have a `table_id` selected, and the `newValue`
        // is different to the current `table_id`, then reset the `fields`
        // to null.
        if (this.values.table_id && this.values.table_id !== newValue) {
          this.values.email_field_id = null
          this.values.name_field_id = null
        }
        this.values.table_id = newValue
      },
    },
    selectedTable() {
      if (!this.values.table_id) {
        return null
      }
      for (const database of this.databases) {
        for (const table of database.tables) {
          if (table.id === this.values.table_id) {
            return table
          }
        }
      }
      return null
    },
    fields() {
      if (!this.selectedTable) {
        return []
      } else {
        return this.selectedTable.fields
      }
    },
    emailFields() {
      return this.fields.filter(({ type }) =>
        this.userSourceType.allowedEmailFieldTypes.includes(type)
      )
    },
    nameFields() {
      return this.fields.filter(({ type }) =>
        this.userSourceType.allowedNameFieldTypes.includes(type)
      )
    },
  },
  methods: {
    getIconForType(type) {
      return this.fieldTypes[type].getIconClass()
    },
  },
}
</script>
