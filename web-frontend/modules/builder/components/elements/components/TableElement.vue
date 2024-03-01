<template>
  <div
    :style="{
      '--button-color': resolveColor(element.button_color, colorVariables),
    }"
    class="table-element"
  >
    <BaserowTable :fields="element.fields" :rows="rows">
      <template #cell-content="{ field, value }">
        <component
          :is="collectionFieldTypes[field.type].component"
          v-bind="value"
        />
      </template>
      <template #empty-state>
        <div class="table-element__empty-message">
          {{ $t('tableElement.empty') }}
        </div>
      </template>
    </BaserowTable>
    <div class="table-element__footer">
      <button
        v-if="hasMorePage"
        class="ab-button"
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
import BaserowTable from '@baserow/modules/builder/components/elements/components/BaserowTable'
import { notifyIf } from '@baserow/modules/core/utils/error'
import _ from 'lodash'

export default {
  name: 'TableElement',
  components: { BaserowTable },
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
      errorNotified: false,
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
    fields() {
      if (!this.element.fields) {
        return []
      }
      return this.element.fields.map((field, index) => ({
        ...field,
        __id__: index,
      }))
    },
    elementContent() {
      if (
        !this.element.data_source_id ||
        !this.getElementContent(this.element) ||
        this.fields.length === 0
      ) {
        return []
      }

      return this.getElementContent(this.element)
    },
    rows() {
      return this.elementContent.map((row, rowIndex) => {
        const newRow = Object.fromEntries(
          this.fields.map((field) => {
            const { name, type } = field
            const fieldType = this.collectionFieldTypes[type]
            return [
              name,
              fieldType.getProps(field, {
                resolveFormula: (formula) =>
                  this.resolveRowFormula(formula, rowIndex),
                applicationContext: this.applicationContext,
              }),
            ]
          })
        )
        newRow.__id__ = uuid()
        return newRow
      })
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
    collectionFieldTypes() {
      return this.$registry.getAll('collectionField')
    },
    dispatchContext() {
      return DataProviderType.getAllDispatchContext(
        this.$registry.getAll('builderDataProvider'),
        this.applicationContext
      )
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
    dispatchContext: {
      handler(newValue, prevValue) {
        if (!_.isEqual(newValue, prevValue)) {
          this.debouncedReset()
        }
      },
      deep: true,
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
      try {
        await this.fetchElementContent({
          element: this.element,
          dataSource: this.dataSource,
          data: this.dispatchContext,
          range,
          replace,
        })
      } catch (error) {
        if (!this.errorNotified) {
          this.errorNotified = true
          notifyIf(error)
        }
      }
    },
    debouncedReset() {
      clearTimeout(this.resetTimeout)
      this.resetTimeout = setTimeout(() => {
        this.errorNotified = false
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
