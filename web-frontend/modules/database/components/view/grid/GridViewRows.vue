<template>
  <div
    class="grid-view__rows"
    :style="{
      transform: `translateY(${rowsTop}px) translateX(${leftOffset}px)`,
    }"
  >
    <GridViewRow
      v-for="row in rows"
      :key="`row-${row.id}`"
      :row="row"
      :fields="fields"
      :all-fields="allFields"
      :field-widths="fieldWidths"
      :include-row-details="includeRowDetails"
      :decorations="augmentedDecorations"
      :read-only="readOnly"
      :can-drag="view.sortings.length === 0"
      :store-prefix="storePrefix"
      v-on="$listeners"
    />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import GridViewRow from '@baserow/modules/database/components/view/grid/GridViewRow'
import gridViewHelpers from '@baserow/modules/database/mixins/gridViewHelpers'

export default {
  name: 'GridViewRows',
  components: { GridViewRow },
  mixins: [gridViewHelpers],
  props: {
    fields: {
      type: Array,
      required: true,
    },
    allFields: {
      type: Array,
      required: true,
    },
    allTableFields: {
      type: Array,
      required: true,
    },
    leftOffset: {
      type: Number,
      required: false,
      default: 0,
    },
    view: {
      type: Object,
      required: true,
    },
    includeRowDetails: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    fieldWidths() {
      const fieldWidths = {}
      this.allFields.forEach((field) => {
        fieldWidths[field.id] = this.getFieldWidth(field.id)
      })
      return fieldWidths
    },
    augmentedDecorations() {
      return this.view.decorations
        .filter(({ value_provider_type: valPro }) => valPro)
        .map((decoration) => {
          const deco = { decoration }

          deco.decorationType = this.$registry.get(
            'viewDecorator',
            decoration.type
          )

          deco.component = deco.decorationType.getComponent()
          deco.place = deco.decorationType.getPlace()

          deco.valueProviderType = this.$registry.get(
            'decoratorValueProvider',
            decoration.value_provider_type
          )

          deco.propsFn = (row) => {
            return {
              value: deco.valueProviderType.getValue({
                row,
                fields: this.allTableFields,
                options: decoration.value_provider_conf,
              }),
            }
          }

          return deco
        })
        .filter(
          ({ decorationType }) =>
            !decorationType.isDeactivated({ view: this.view })
        )
    },
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        rows: this.$options.propsData.storePrefix + 'view/grid/getRows',
        rowsTop: this.$options.propsData.storePrefix + 'view/grid/getRowsTop',
      }),
    }
  },
}
</script>
