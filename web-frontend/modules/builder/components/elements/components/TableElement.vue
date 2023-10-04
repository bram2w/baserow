<template>
  <table class="table-element">
    <thead>
      <tr class="table-element__header-row">
        <th
          v-for="field in element.fields"
          :key="field.id"
          class="table-element__header-cell"
        >
          {{ field.name }}
        </th>
      </tr>
    </thead>
    <tbody v-if="dataSourceContent.length">
      <tr
        v-for="(row, index) in dataSourceContent"
        :key="row.__id__"
        class="table-element__row"
      >
        <td
          v-for="field in element.fields"
          :key="field.id"
          class="table-element__cell"
        >
          {{ resolveRowFormula(field.value, index) }}
        </td>
      </tr>
    </tbody>
    <tbody v-else>
      <tr>
        <td
          class="table-element__empty-message"
          :colspan="element.fields.length"
        >
          {{ $t('tableElement.empty') }}
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'
import RuntimeFormulaContext from '@baserow/modules/core/runtimeFormulaContext'
import { resolveFormula } from '@baserow/modules/core/formula'
import { uuid } from '@baserow/modules/core/utils/string'

export default {
  name: 'TableElement',
  mixins: [element],
  props: {
    /**
     * @type {Object}
     * @property {int} data_source_id - The collection data source Id we want to
     *   display.
     * @property {Object} fields - The fields of the data source.
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    dataSource() {
      if (!this.element.data_source_id) {
        return null
      }
      return this.$store.getters['dataSource/getPageDataSourceById'](
        this.page,
        this.element.data_source_id
      )
    },
    dataSourceContent() {
      if (!this.element.data_source_id) {
        return []
      }
      // Here we add a temporary __id__ property for the "v-for key"
      return (
        this.$store.getters['dataSourceContent/getDataSourceContents'](
          this.page
        )[this.element.data_source_id] || []
      ).map((row) => ({ ...row, __id__: uuid() }))
    },
  },
  methods: {
    resolveRowFormula(formula, index) {
      const formulaContext = new Proxy(
        new RuntimeFormulaContext(
          this.$registry.getAll('builderDataProvider'),
          {
            builder: this.builder,
            page: this.page,
            mode: this.mode,
            element: this.element,
            recordIndex: index,
          }
        ),
        {
          get(target, prop) {
            return target.get(prop)
          },
        }
      )
      try {
        return resolveFormula(formula, this.formulaFunctions, formulaContext)
      } catch {
        return ''
      }
    },
  },
}
</script>
