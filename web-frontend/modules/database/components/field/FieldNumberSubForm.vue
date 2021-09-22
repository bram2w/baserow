<template>
  <div>
    <div class="control">
      <label class="control__label control__label--small">{{
        $t('fieldNumberSubForm.typeLabel')
      }}</label>
      <div class="control__elements">
        <Dropdown
          v-model="values.number_type"
          :class="{ 'dropdown--error': $v.values.number_type.$error }"
          @hide="$v.values.number_type.$touch()"
        >
          <DropdownItem
            :name="$t('fieldNumberSubForm.integer') + ' (1)'"
            value="INTEGER"
          ></DropdownItem>
          <DropdownItem
            :name="$t('fieldNumberSubForm.decimal') + ' (1.0)'"
            value="DECIMAL"
          ></DropdownItem>
        </Dropdown>
      </div>
    </div>
    <div v-show="values.number_type === 'DECIMAL'" class="control">
      <label class="control__label control__label--small">{{
        $t('fieldNumberSubForm.decimalPlacesLabel')
      }}</label>
      <div class="control__elements">
        <Dropdown
          v-model="values.number_decimal_places"
          :class="{ 'dropdown--error': $v.values.number_decimal_places.$error }"
          @hide="$v.values.number_decimal_places.$touch()"
        >
          <DropdownItem name="1.0" :value="1"></DropdownItem>
          <DropdownItem name="1.00" :value="2"></DropdownItem>
          <DropdownItem name="1.000" :value="3"></DropdownItem>
          <DropdownItem name="1.0000" :value="4"></DropdownItem>
          <DropdownItem name="1.00000" :value="5"></DropdownItem>
        </Dropdown>
      </div>
    </div>
    <div class="control">
      <div class="control__elements">
        <Checkbox v-model="values.number_negative">{{
          $t('fieldNumberSubForm.allowNegative')
        }}</Checkbox>
      </div>
    </div>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'

export default {
  name: 'FieldNumberSubForm',
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: [
        'number_type',
        'number_decimal_places',
        'number_negative',
      ],
      values: {
        number_type: 'INTEGER',
        number_decimal_places: 1,
        number_negative: false,
      },
    }
  },
  validations: {
    values: {
      number_type: { required },
      number_decimal_places: { required },
    },
  },
}
</script>

<i18n>
{
  "en": {
    "fieldNumberSubForm": {
      "typeLabel": "Number type",
      "integer": "Integer",
      "decimal": "Decimal",
      "decimalPlacesLabel": "Decimal places",
      "allowNegative": "Allow negative"
    }
  },
  "fr": {
    "fieldNumberSubForm": {
      "typeLabel": "Type numérique",
      "integer": "Entier",
      "decimal": "Décimal",
      "decimalPlacesLabel": "Précision",
      "allowNegative": "Autoriser les nombres négatifs"
    }
  }
}
</i18n>
