<template>
  <div
    ref="fieldContextAnchor"
    class="grid-view-aggregation"
    :class="{ 'read-only': readOnly }"
    @click.prevent="
      !readOnly &&
        $refs[`fieldContext`].toggle(
          $refs.fieldContextAnchor,
          'top',
          'right',
          10
        )
    "
  >
    <component
      :is="viewAggregationType.getComponent()"
      v-if="viewAggregationType"
      :loading="loading"
      :aggregation-type="viewAggregationType"
      :value="value"
    />
    <Context :ref="`fieldContext`">
      <ul class="select__items">
        <li
          class="select__item select__item--no-options"
          :class="{ active: !viewAggregationType }"
        >
          <a class="select__item-link" @click="selectAggregation('none')"
            ><div class="select__item-name">{{ $t('common.none') }}</div></a
          >
        </li>
        <li
          v-for="viewAggregation in viewAggregationTypes"
          :key="viewAggregation.getType()"
          class="select__item select__item--no-options"
          :class="{
            active: viewAggregation === viewAggregationType,
          }"
        >
          <a
            class="select__item-link"
            @click="selectAggregation(viewAggregation.getType())"
            ><div class="select__item-name">
              {{ viewAggregation.getName() }}
            </div></a
          >
        </li>
      </ul>
    </Context>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'GridViewFieldFooter',
  props: {
    field: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: false,
      default: false,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  computed: {
    aggregationType() {
      return this.fieldOptions[this.field.id]?.aggregation_type
    },
    value() {
      if (this.fieldAggregationData[this.field.id] !== undefined) {
        const { value } = this.fieldAggregationData[this.field.id]

        return this.viewAggregationType.getValue(value, {
          rowCount: this.rowCount,
          field: this.field,
          fieldType: this.fieldType,
        })
      } else {
        return undefined
      }
    },
    loading() {
      return this.fieldAggregationData[this.field.id]?.loading
    },
    viewAggregationType() {
      if (!this.aggregationType) {
        return null
      }
      return this.$registry.get('viewAggregation', this.aggregationType)
    },
    viewAggregationTypes() {
      return this.$registry
        .getOrderedList('viewAggregation')
        .filter((agg) => agg.fieldIsCompatible(this.field))
    },
    fieldType() {
      return this.$registry.get('field', this.field.type)
    },
  },
  watch: {
    aggregationType(value) {
      if (!value) {
        return
      }
      this.$store.dispatch(
        this.storePrefix + 'view/grid/fetchFieldAggregationData',
        {
          view: this.view,
          fieldId: this.field.id,
          options: {
            aggregation_raw_type: this.viewAggregationType.getRawType(),
            aggregation_type: this.viewAggregationType.getType(),
          },
        }
      )
    },
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        fieldAggregationData:
          this.$options.propsData.storePrefix +
          'view/grid/getAllFieldAggregationData',
        fieldOptions:
          this.$options.propsData.storePrefix + 'view/grid/getAllFieldOptions',
        rowCount: this.$options.propsData.storePrefix + 'view/grid/getCount',
      }),
    }
  },
  methods: {
    async selectAggregation(newType) {
      this.$refs.fieldContext.hide()

      const values = {
        aggregation_type: '',
        aggregation_raw_type: '',
      }

      if (newType !== 'none') {
        const selectedAggregation = this.$registry.get(
          'viewAggregation',
          newType
        )
        values.aggregation_type = newType
        values.aggregation_raw_type = selectedAggregation.getRawType()
      }

      await this.$store.dispatch(
        this.storePrefix + 'view/grid/updateFieldOptionsOfField',
        {
          field: this.field,
          values,
        }
      )
    },
  },
}
</script>
