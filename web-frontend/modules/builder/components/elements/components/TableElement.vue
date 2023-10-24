<template>
  <div>
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
      <tbody v-if="elementContent.length">
        <tr
          v-for="(row, index) in elementContent"
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
    <div class="table-element__footer">
      <button
        v-if="hasMorePage"
        class="link-button-element-button"
        :disabled="loading"
        @click="loadMore()"
      >
        {{ $t('tableElement.showMore') }}
      </button>
    </div>
  </div>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'
import RuntimeFormulaContext from '@baserow/modules/core/runtimeFormulaContext'
import { resolveFormula } from '@baserow/modules/core/formula'
import { uuid } from '@baserow/modules/core/utils/string'
import { mapActions, mapGetters } from 'vuex'
import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'

export default {
  name: 'TableElement',
  mixins: [element],
  props: {
    /**
     * @type {Object}
     * @property {int} data_source_id - The collection data source Id we want to
     *   display.
     * @property {Object} fields - The fields of the data source.
     * @property {int} items_per_page - The number of items per page.
     */
    element: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      // The first page has been loaded by the data provider at page load already
      currentOffset: this.element.items_per_page,
      resetTimeout: null,
    }
  },
  computed: {
    ...mapGetters({
      getLoading: 'elementContent/getLoading',
      getHasMorePage: 'elementContent/getHasMorePage',
      getElementContent: 'elementContent/getElementContent',
      getReset: 'elementContent/getReset',
      getPageDataSourceById: 'dataSource/getPageDataSourceById',
    }),
    dataSource() {
      if (!this.element.data_source_id) {
        return null
      }
      return this.getPageDataSourceById(this.page, this.element.data_source_id)
    },
    elementContent() {
      if (!this.element.data_source_id) {
        return []
      }
      // Here we add a temporary __id__ property for the "v-for key"
      return this.getElementContent(this.element).map((row) => ({
        ...row,
        __id__: uuid(),
      }))
    },
    hasMorePage() {
      return this.getHasMorePage(this.element)
    },
    loading() {
      return this.getLoading(this.element)
    },
    reset() {
      return this.getReset(this.element)
    },
  },
  watch: {
    reset() {
      this.debouncedReset()
    },
    'element.data_source_id'() {
      this.debouncedReset()
    },
    'element.items_per_page'() {
      this.debouncedReset()
    },
  },
  async mounted() {
    if (this.element.data_source_id) {
      await this.fetchContent([0, this.element.items_per_page])
    }
  },
  methods: {
    ...mapActions({
      fetchElementContent: 'elementContent/fetchElementContent',
      clearElementContent: 'elementContent/clearElementContent',
    }),
    async fetchContent(range, replace) {
      const dispatchContext = DataProviderType.getAllBackendContext(
        this.$registry.getAll('builderDataProvider'),
        this.applicationContext
      )

      await this.fetchElementContent({
        element: this.element,
        dataSource: this.dataSource,
        data: dispatchContext,
        range,
        replace,
      })
    },
    debouncedReset() {
      clearTimeout(this.resetTimeout)
      this.resetTimeout = setTimeout(() => {
        this.currentOffset = 0
        this.loadMore(true)
      }, 500)
    },
    resolveRowFormula(formula, index) {
      const formulaContext = new Proxy(
        new RuntimeFormulaContext(
          this.$registry.getAll('builderDataProvider'),
          {
            ...this.applicationContext,
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
    async loadMore(replace = false) {
      await this.fetchContent(
        [this.currentOffset, this.element.items_per_page],
        replace
      )

      this.currentOffset += this.element.items_per_page
    },
  },
}
</script>
