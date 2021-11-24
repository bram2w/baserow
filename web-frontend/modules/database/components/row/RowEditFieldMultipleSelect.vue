<template>
  <div class="control__elements">
    <ul class="field-multiple-select__items">
      <li
        v-for="item in value"
        :key="item.id"
        class="field-multiple-select__item"
        :class="'background-color--' + item.color"
      >
        <div class="field-multiple-select__name">
          {{ item.value }}
        </div>
        <a
          v-if="!readOnly"
          class="field-multiple-select__remove"
          @click.prevent="removeValue($event, value, item.id)"
        >
          <i class="fas fa-times"></i>
        </a>
      </li>
    </ul>
    <a
      v-if="!readOnly"
      ref="dropdownLink"
      class="add"
      @click.prevent="toggleDropdown()"
    >
      <i class="fas fa-plus add__icon"></i>
      {{ $t('rowEditFieldMultipleSelect.addOption') }}
    </a>
    <FieldSelectOptionsDropdown
      ref="dropdown"
      :options="availableSelectOptions"
      :allow-create-option="true"
      :disabled="readOnly"
      :show-input="false"
      :show-empty-value="false"
      :class="{ 'dropdown--error': touched && !valid }"
      @input="updateValue($event, value)"
      @create-option="createOption($event)"
      @hide="touch()"
    ></FieldSelectOptionsDropdown>
    <div v-show="touched && !valid" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import selectOptions from '@baserow/modules/database/mixins/selectOptions'
import multipleSelectField from '@baserow/modules/database/mixins/multipleSelectField'

export default {
  name: 'RowEditFieldMultipleSelect',
  mixins: [rowEditField, selectOptions, multipleSelectField],
}
</script>

<i18n>
{
  "en": {
    "rowEditFieldMultipleSelect": {
      "addOption": "Add another option"
    }
  },
  "fr": {
    "rowEditFieldMultipleSelect": {
      "addOption": "Ajouter une option"
    }
  }
}
</i18n>
