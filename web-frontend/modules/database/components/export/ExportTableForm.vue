<template>
  <form @submit.prevent="submit">
    <div class="row">
      <div class="col col-12">
        <div class="control">
          <label class="control__label">Select the view to export:</label>
          <div class="control__elements">
            <ExportTableDropdown
              v-model="values.view_id"
              :views="views"
              :loading="loading"
              @input="values.exporter_type = firstExporterType"
            ></ExportTableDropdown>
          </div>
        </div>
        <ExporterTypeChoices
          v-model="values.exporter_type"
          :exporter-types="exporterTypes"
          :loading="loading"
        ></ExporterTypeChoices>
        <div v-if="$v.values.exporter_type.$error" class="error">
          No exporter type available please select a different view or entire
          table.
        </div>
      </div>
    </div>
    <component
      :is="exporterComponent"
      :loading="loading"
      @values-changed="$emit('values-changed', values)"
    />
    <slot></slot>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

import ExportTableDropdown from '@baserow/modules/database/components/export/ExportTableDropdown'
import ExporterTypeChoices from '@baserow/modules/database/components/export/ExporterTypeChoices'

export default {
  name: 'ExportTableForm',
  components: {
    ExporterTypeChoices,
    ExportTableDropdown,
  },
  mixins: [form],
  props: {
    view: {
      type: Object,
      required: false,
      default: null,
    },
    views: {
      type: Array,
      required: true,
    },
    loading: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      values: {
        view_id: this.view === null ? null : this.view.id,
        exporter_type: null,
      },
    }
  },
  computed: {
    selectedView() {
      return this.views.find((view) => view.id === this.values.view_id) || null
    },
    exporterTypes() {
      const types = Object.values(this.$registry.getAll('exporter'))
      return types.filter((exporterType) => {
        if (this.selectedView !== null) {
          return exporterType
            .getSupportedViews()
            .includes(this.selectedView.type)
        } else {
          return exporterType.getCanExportTable()
        }
      })
    },
    firstExporterType() {
      return this.exporterTypes.length > 0 ? this.exporterTypes[0].type : null
    },
    exporterComponent() {
      if (!this.values.exporter_type) {
        return null
      }

      return this.exporterTypes
        .find((exporterType) => exporterType.type === this.values.exporter_type)
        .getFormComponent()
    },
  },
  created() {
    this.values.exporter_type = this.firstExporterType
  },
  validations: {
    values: {
      exporter_type: { required },
    },
  },
}
</script>
