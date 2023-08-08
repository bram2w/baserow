<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('columnElementForm.columnAmountTitle') }}
      </label>
      <div class="control__elements">
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
      </div>
    </FormElement>
    <FormElement class="control">
      <FormInput
        v-model="values.column_gap"
        :label="$t('columnElementForm.columnGapTitle')"
        :placeholder="$t('columnElementForm.columnGapPlaceholder')"
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
        type="number"
        @blur="$v.values.column_gap.$touch()"
      ></FormInput>
    </FormElement>
    <FormElement class="control">
      <VerticalAlignmentSelector v-model="values.alignment" />
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { VERTICAL_ALIGNMENTS } from '@baserow/modules/builder/enums'
import { required, integer, minValue, maxValue } from 'vuelidate/lib/validators'
import VerticalAlignmentSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/VerticalAlignmentSelector'

export default {
  name: 'ColumnElementForm',
  components: {
    VerticalAlignmentSelector,
  },
  mixins: [form],
  data() {
    return {
      values: {
        column_amount: 1,
        column_gap: 30,
        alignment: VERTICAL_ALIGNMENTS.TOP.value,
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
