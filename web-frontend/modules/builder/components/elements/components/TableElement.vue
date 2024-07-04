<template>
  <div class="table-element">
    <BaserowTable
      :fields="element.fields"
      :rows="rows"
      :orientation="orientation"
    >
      <template #cell-content="{ rowIndex, field, value }">
        <component
          :is="collectionFieldTypes[field.type].component"
          :element="element"
          :field="field"
          :application-context-additions="{
            recordIndex: rowIndex,
            recordIndexPath: [...applicationContext.recordIndexPath, rowIndex],
            field,
          }"
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
      <ABButton
        v-if="hasMorePage"
        :style="getStyleOverride('button')"
        :disabled="contentLoading"
        :loading="contentLoading"
        @click="loadMore()"
      >
        {{ resolvedButtonLoadMoreLabel || $t('tableElement.showMore') }}
      </ABButton>
    </div>
  </div>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'
import RuntimeFormulaContext from '@baserow/modules/core/runtimeFormulaContext'
import { uuid } from '@baserow/modules/core/utils/string'
import BaserowTable from '@baserow/modules/builder/components/elements/components/BaserowTable'
import collectionElement from '@baserow/modules/builder/mixins/collectionElement'
import { ensureString } from '@baserow/modules/core/utils/validator'

export default {
  name: 'TableElement',
  components: { BaserowTable },
  mixins: [element, collectionElement],
  props: {
    /**
     * @type {Object}
     * @property {int} data_source_id - The collection data source Id we want to
     *   display.
     * @property {Object} fields - The fields of the data source.
     * @property {int} items_per_page - The number of items per page.
     * @property {string} button_color - The color of the button.
     * @property {string} orientation - The orientation for eaceh device.
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    fields() {
      if (!this.element.fields) {
        return []
      }
      return this.element.fields.map((field, index) => ({
        ...field,
        __id__: index,
      }))
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
    collectionFieldTypes() {
      return this.$registry.getAll('collectionField')
    },
    orientation() {
      const device = this.$store.getters['page/getDeviceTypeSelected']
      return this.element.orientation[device]
    },
    resolvedButtonLoadMoreLabel() {
      return ensureString(
        this.resolveFormula(this.element.button_load_more_label)
      )
    },
  },

  methods: {
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
        return ensureString(this.resolveFormula(formula, formulaContext))
      } catch {
        return ''
      }
    },
  },
}
</script>
