<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormGroup :label="$t('columnElementForm.columnAmountTitle')">
      <Dropdown v-model="values.column_amount" :show-search="false">
        <DropdownItem
          v-for="columnAmount in columnAmounts"
          :key="columnAmount.value"
          :name="columnAmount.name"
          :value="columnAmount.value"
        >
          {{ columnAmount.name }}
        </DropdownItem>
      </Dropdown>
    </FormGroup>
    <FormGroup
      :label="$t('columnElementForm.columnGapTitle')"
      :error="
        $v.values.column_gap.$dirty && !$v.values.column_gap.required
          ? $t('error.requiredField')
          : !$v.values.column_gap.integer
          ? $t('error.integerField')
          : !$v.values.column_gap.minValue
          ? $t('error.minValueField', { min: 0 })
          : !$v.values.column_gap.maxValue
          ? $t('error.maxValueField', { max: 2000 })
          : ''
      "
    >
      <FormInput
        v-model="values.column_gap"
        no-control
        type="number"
        @blur="$v.values.column_gap.$touch()"
      />
    </FormGroup>
    <FormGroup :label="$t('columnElementForm.verticalAlignment')">
      <VerticalAlignmentSelector v-model="values.alignment" />
    </FormGroup>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { VERTICAL_ALIGNMENTS } from '@baserow/modules/builder/enums'
import { required, integer, minValue, maxValue } from 'vuelidate/lib/validators'
import VerticalAlignmentSelector from '@baserow/modules/builder/components/VerticalAlignmentSelector'
import elementForm from '@baserow/modules/builder/mixins/elementForm'

export default {
  name: 'ColumnElementForm',
  components: {
    VerticalAlignmentSelector,
  },
  mixins: [elementForm],
  data() {
    return {
      values: {
        column_amount: 1,
        column_gap: 30,
        alignment: VERTICAL_ALIGNMENTS.TOP,
      },
    }
  },
  computed: {
    columnAmounts() {
      const maximumColumnAmount = 6
      return [...Array(maximumColumnAmount).keys()].map((columnAmount) => ({
        name: this.$tc('columnElementForm.columnAmountName', columnAmount + 1, {
          columnAmount: columnAmount + 1,
        }),
        value: columnAmount + 1,
      }))
    },
  },
  methods: {
    emitChange(newValues) {
      if (this.isFormValid()) {
        form.methods.emitChange.bind(this)(newValues)
      }
    },
  },
  validations: {
    values: {
      column_gap: {
        required,
        integer,
        minValue: minValue(0),
        maxValue: maxValue(2000),
      },
    },
  },
}
</script>
