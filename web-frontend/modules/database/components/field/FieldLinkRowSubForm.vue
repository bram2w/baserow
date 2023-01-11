<template>
  <div>
    <div class="control">
      <div v-if="tables.length > 0">
        <label class="control__label control__label--small">
          {{ $t('fieldLinkRowSubForm.selectTableLabel') }}
        </label>
        <div class="control__elements">
          <Dropdown
            v-model="values.link_row_table_id"
            :class="{ 'dropdown--error': $v.values.link_row_table_id.$error }"
            :disabled="!isSelectedFieldAccessible"
            @hide="$v.values.link_row_table_id.$touch()"
          >
            <DropdownItem
              v-for="table in tablesWhereFieldsCanBeCreated"
              :key="table.id"
              :name="table.name"
              :value="table.id"
            ></DropdownItem>
          </Dropdown>
          <div v-if="$v.values.link_row_table_id.$error" class="error">
            {{ $t('error.requiredField') }}
          </div>
        </div>
      </div>
    </div>
    <div v-show="values.link_row_table_id !== table.id" class="control">
      <div class="control__elements">
        <Checkbox v-model="values.has_related_field">{{
          $t('fieldLinkRowSubForm.hasRelatedFieldLabel')
        }}</Checkbox>
      </div>
    </div>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'

export default {
  name: 'FieldLinkRowSubForm',
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['link_row_table_id', 'has_related_field'],
      values: {
        link_row_table_id: null,
        has_related_field: true,
      },
      initialLinkRowTableId: null,
    }
  },
  computed: {
    tables() {
      const applications = this.$store.getters['application/getAll']
      const databaseType = DatabaseApplicationType.getType()
      const databaseId = this.table.database_id
      // Search for the database of the related table and return all the siblings of
      // that table because those are the only ones the user can choose form.
      for (let i = 0; i < applications.length; i++) {
        const application = applications[i]
        if (
          application.type === databaseType &&
          application.id === databaseId
        ) {
          return application.tables
        }
      }
      return []
    },
    database() {
      return this.$store.getters['application/get'](this.table.database_id)
    },
    tablesWhereFieldsCanBeCreated() {
      return this.tables.filter((table) =>
        this.$hasPermission(
          'database.table.create_field',
          table,
          this.database.group.id
        )
      )
    },
    canDeleteInSelectedFieldTable() {
      return (
        this.selectedFieldTable &&
        this.$hasPermission(
          'database.table.field.delete_related_link_row_field',
          this.selectedFieldTable,
          this.database.group.id
        )
      )
    },
    selectedFieldTable() {
      return this.tablesWhereFieldsCanBeCreated.find(
        (table) => table.id === this.values?.link_row_table_id
      )
    },
    isSelectedFieldAccessible() {
      return (
        this.values?.link_row_table_id === null ||
        this.canDeleteInSelectedFieldTable
      )
    },
  },
  mounted() {
    this.initialLinkRowTable = this.values.link_row_table_id
    this.values.has_related_field =
      this.initialLinkRowTable == null ||
      this.defaultValues.link_row_related_field != null
  },
  validations: {
    values: {
      link_row_table_id: { required },
    },
  },
  methods: {
    reset() {
      this.initialLinkRowTable = this.values.link_row_table_id
      this.defaultValues.has_related_field =
        this.initialLinkRowTable == null ||
        this.defaultValues.link_row_related_field != null
      return form.methods.reset.call(this)
    },
    isValid() {
      return form.methods.isValid().call(this) && this.tables.length > 0
    },
    getFormValues() {
      const data = form.methods.getFormValues.call(this)
      // self-referencing link-row fields cannot have the related field
      if (this.values.link_row_table_id === this.table.id) {
        data.has_related_field = false
      }
      return data
    },
  },
}
</script>
