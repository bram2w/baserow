<template>
  <Modal>
    <h2 class="box__title">{{ $t('createTableModal.title') }}</h2>
    <Error :error="error"></Error>
    <TableForm ref="tableForm" @submitted="submitted">
      <div class="control">
        <label class="control__label">
          {{ $t('createTableModal.importLabel') }}
        </label>
        <div class="control__elements">
          <ul class="choice-items">
            <li>
              <a
                class="choice-items__link"
                :class="{ active: importer === '' }"
                @click="importer = ''"
              >
                <i class="choice-items__icon fas fa-clone"></i>
                {{ $t('createTableModal.newTable') }}
              </a>
            </li>
            <li v-for="importerType in importerTypes" :key="importerType.type">
              <a
                class="choice-items__link"
                :class="{ active: importer === importerType.type }"
                @click="importer = importerType.type"
              >
                <i
                  class="choice-items__icon fas"
                  :class="'fa-' + importerType.iconClass"
                ></i>
                {{ importerType.getName() }}
              </a>
            </li>
          </ul>
        </div>
      </div>
      <component :is="importerComponent" />
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
          >
            {{ $t('createTableModal.addButton') }}
          </button>
        </div>
      </div>
    </TableForm>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'

import TableForm from './TableForm'

export default {
  name: 'CreateTableModal',
  components: { TableForm },
  mixins: [modal, error],
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      importer: '',
    }
  },
  computed: {
    importerTypes() {
      return this.$registry.getAll('importer')
    },
    importerComponent() {
      return this.importer === ''
        ? null
        : this.$registry.get('importer', this.importer).getFormComponent()
    },
  },
  methods: {
    hide(...args) {
      modal.methods.hide.call(this, ...args)
      this.importer = ''
    },
    /**
     * When the form is submitted we try to extract the initial data and first row
     * header setting from the values. An importer could have added those, but they
     * need to be removed from the values.
     */
    async submitted(values) {
      this.loading = true
      this.hideError()

      let firstRowHeader = false
      let data = null

      if (Object.prototype.hasOwnProperty.call(values, 'firstRowHeader')) {
        firstRowHeader = values.firstRowHeader
        delete values.firstRowHeader
      }

      if (Object.prototype.hasOwnProperty.call(values, 'data')) {
        data = JSON.parse(values.data)
        delete values.data
      }

      try {
        const table = await this.$store.dispatch('table/create', {
          database: this.application,
          values,
          initialData: data,
          firstRowHeader,
        })
        this.loading = false
        this.hide()

        // Redirect to the newly created table.
        this.$nuxt.$router.push({
          name: 'database-table',
          params: {
            databaseId: this.application.id,
            tableId: table.id,
          },
        })
      } catch (error) {
        this.loading = false
        this.handleError(error, 'application')
      }
    },
  },
}
</script>

<i18n>
{
  "en": {
    "createTableModal": {
      "title": "Create new table",
      "importLabel": "Would you like to import existing data?",
      "newTable": "Start with a new table",
      "addButton": "Add table"
    }
  },
  "fr": {
    "createTableModal": {
      "title": "Créer une nouvelle table",
      "importLabel": "Souhaitez-vous importer des données existantes ?",
      "newTable": "Commencer avec une table vide",
      "addButton": "Ajouter la table"
    }
  }
}
</i18n>
