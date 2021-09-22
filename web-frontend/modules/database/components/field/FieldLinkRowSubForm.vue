<template>
  <div>
    <div class="control">
      <div v-if="tables.length === 0" class="alert alert--error context__alert">
        <p class="alert__content">
          {{ $t('fieldLinkRowSubForm.noTable') }}
        </p>
      </div>
      <div v-if="tables.length > 0">
        <label class="control__label control__label--small">
          {{ $t('fieldLinkRowSubForm.selectTableLabel') }}
        </label>
        <div class="control__elements">
          <Dropdown
            v-model="values.link_row_table"
            :class="{ 'dropdown--error': $v.values.link_row_table.$error }"
            @hide="$v.values.link_row_table.$touch()"
          >
            <DropdownItem
              v-for="table in tables"
              :key="table.id"
              :name="table.name"
              :value="table.id"
            ></DropdownItem>
          </Dropdown>
          <div v-if="$v.values.link_row_table.$error" class="error">
            {{ $t('error.requiredField') }}
          </div>
          <div
            v-show="
              initialLinkRowTable !== null &&
              initialLinkRowTable !== values.link_row_table
            "
            class="alert alert--warning context__alert"
          >
            <p class="alert__content">
              {{ $t('fieldLinkRowSubForm.dataLost') }}
            </p>
          </div>
        </div>
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
      allowedValues: ['link_row_table'],
      values: {
        link_row_table: null,
      },
      initialLinkRowTable: null,
    }
  },
  computed: {
    tables() {
      const applications = this.$store.getters['application/getAll']
      const databaseType = DatabaseApplicationType.getType()
      const tableId = this.table.id

      // Search for the database of the related table and return all the siblings of
      // that table because those are the only ones the user can choose form.
      for (let i = 0; i < applications.length; i++) {
        const application = applications[i]
        if (application.type === databaseType) {
          for (let tableI = 0; tableI < application.tables.length; tableI++) {
            const table = application.tables[tableI]
            if (table.id === tableId) {
              return application.tables.filter((t) => t.id !== tableId)
            }
          }
        }
      }

      return []
    },
  },
  mounted() {
    this.initialLinkRowTable = this.values.link_row_table
  },
  validations: {
    values: {
      link_row_table: { required },
    },
  },
  methods: {
    reset() {
      this.initialLinkRowTable = this.values.link_row_table
      return form.methods.reset.call(this)
    },
    isValid() {
      return form.methods.isValid().call(this) && this.tables.length > 0
    },
  },
}
</script>

<i18n>
{
  "en": {
    "fieldLinkRowSubForm": {
      "noTable": "You need at least one other table in the same database to link to.",
      "selectTableLabel": "Select a table to link to",
      "dataLost": "By changing the table, all data will be lost."
    }
  },
  "fr": {
    "fieldLinkRowSubForm": {
      "noTable": "Vous devez créer au moins une autre table dans la même base de données pour pouvoir créer un lien.",
      "selectTableLabel": "Sélectionnez une table",
      "dataLost": "En modifiant la table, toutes les données de la colonne seront supprimées"
    }
  }
}
</i18n>
