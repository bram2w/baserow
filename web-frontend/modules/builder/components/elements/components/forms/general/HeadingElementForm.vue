<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('headingElementForm.levelTitle') }}
      </label>
      <div class="control__elements">
        <Dropdown v-model="values.level" :show-search="false">
          <DropdownItem
            v-for="level in levels"
            :key="level.value"
            :name="level.name"
            :value="level.value"
          >
            {{ level.name }}
          </DropdownItem>
        </Dropdown>
      </div>
    </FormElement>
    <FormulaInputGroup
      v-model="values.value"
      :label="$t('headingElementForm.textTitle')"
      :placeholder="$t('elementForms.textInputPlaceholder')"
      :error="
        !$v.values.value.validFormula ? $t('elementForms.invalidFormula') : ''
      "
    />
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import FormulaInputGroup from '@baserow/modules/core/components/formula/FormulaInputGroup'
import { isValidFormula } from '@baserow/formula'

export default {
  name: 'HeaderElementForm',
  components: { FormulaInputGroup },
  mixins: [form],
  props: {},
  data() {
    return {
      values: {
        value: '',
        level: 1,
      },
      levels: [...Array(6).keys()].map((level) => ({
        name: this.$t('headingElementForm.headingName', { level: level + 1 }),
        value: level + 1,
      })),
    }
  },
  validations() {
    return {
      values: {
        value: { validFormula: isValidFormula },
      },
    }
  },
}
</script>
