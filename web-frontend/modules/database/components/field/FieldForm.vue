<template>
  <form class="context__form" @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('name')" class="control">
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': fieldHasErrors('name') }"
          type="text"
          class="input input--small"
          :placeholder="$t('fieldForm.name')"
          @blur="$v.values.name.$touch()"
          @input="isPrefilledWithSuggestedFieldName = false"
          @keydown.enter="handleKeydownEnter($event)"
        />
        <div
          v-if="$v.values.name.$dirty && !$v.values.name.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
        <div
          v-else-if="
            $v.values.name.$dirty && !$v.values.name.mustHaveUniqueFieldName
          "
          class="error"
        >
          {{ $t('fieldForm.fieldAlreadyExists') }}
        </div>
        <div
          v-else-if="
            $v.values.name.$dirty &&
            !$v.values.name.mustNotClashWithReservedName
          "
          class="error"
        >
          {{ $t('error.nameNotAllowed') }}
        </div>
        <div
          v-else-if="$v.values.name.$dirty && !$v.values.name.maxLength"
          class="error"
        >
          {{ $t('error.nameTooLong') }}
        </div>
      </div>
    </FormElement>
    <div v-if="forcedType === null" class="control">
      <div class="control__elements">
        <Dropdown
          ref="fieldTypesDropdown"
          v-model="values.type"
          :class="{ 'dropdown--error': $v.values.type.$error }"
          :fixed-items="true"
          small
          @hide="$v.values.type.$touch()"
        >
          <DropdownItem
            v-for="(fieldType, type) in fieldTypes"
            :key="type"
            :icon="fieldType.iconClass"
            :name="fieldType.getName()"
            :value="fieldType.type"
            :disabled="primary && !fieldType.canBePrimaryField"
          ></DropdownItem>
        </Dropdown>
        <div v-if="$v.values.type.$error" class="error">
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </div>
    <template v-if="hasFormComponent">
      <component
        :is="getFormComponent(values.type)"
        ref="childForm"
        :table="table"
        :field-type="values.type"
        :view="view"
        :primary="primary"
        :name="values.name"
        :default-values="defaultValues"
        @validate="$v.$touch"
        @suggested-field-name="handleSuggestedFieldName($event)"
      />
    </template>
    <slot></slot>
  </form>
</template>

<script>
import { mapGetters } from 'vuex'
import { required, maxLength } from 'vuelidate/lib/validators'

import { getNextAvailableNameInSequence } from '@baserow/modules/core/utils/string'
import form from '@baserow/modules/core/mixins/form'
import {
  RESERVED_BASEROW_FIELD_NAMES,
  MAX_FIELD_NAME_LENGTH,
} from '@baserow/modules/database/utils/constants'

// @TODO focus form on open
export default {
  name: 'FieldForm',
  mixins: [form],
  props: {
    table: {
      type: Object,
      required: true,
    },
    view: {
      type: [Object, null],
      required: false,
      default: null,
    },
    primary: {
      type: Boolean,
      required: false,
      default: false,
    },
    forcedType: {
      type: [String, null],
      required: false,
      default: null,
    },
  },
  data() {
    return {
      allowedValues: ['name', 'type'],
      values: {
        name: '',
        type: this.forcedType || '',
      },
      isPrefilledWithSuggestedFieldName: false,
      oldValueType: null,
    }
  },
  computed: {
    fieldTypes() {
      return this.$registry.getAll('field')
    },
    hasFormComponent() {
      return !!this.values.type && this.getFormComponent(this.values.type)
    },
    existingFieldId() {
      return this.defaultValues ? this.defaultValues.id : null
    },
    ...mapGetters({
      fields: 'field/getAll',
    }),
    isNameFieldEmptyOrPrefilled() {
      return (
        this.values.name === '' ||
        this.values.name ===
          this.getNextAvailableFieldName(
            this.fieldTypes[this.oldValueType]?.getName()
          ) ||
        this.values.name ===
          this.getNextAvailableFieldName(
            this.fieldTypes[this.values.type]?.getName()
          ) ||
        this.isPrefilledWithSuggestedFieldName
      )
    },
  },
  watch: {
    // if the name field is empty or prefilled by a default value
    // we want to update the name field with the name of the field type
    // when the field type is changed.
    'values.type'(newValueType, oldValueType) {
      this.oldValueType = oldValueType
      if (this.isNameFieldEmptyOrPrefilled) {
        const availableFieldName = this.getNextAvailableFieldName(
          this.fieldTypes[newValueType]?.getName()
        )
        this.values.name = availableFieldName
      }
      this.isPrefilledWithSuggestedFieldName = false
    },
  },
  validations() {
    return {
      values: {
        name: {
          required,
          maxLength: maxLength(MAX_FIELD_NAME_LENGTH),
          mustHaveUniqueFieldName: this.mustHaveUniqueFieldName,
          mustNotClashWithReservedName: this.mustNotClashWithReservedName,
        },
        type: { required },
      },
    }
  },
  methods: {
    mustHaveUniqueFieldName(param) {
      let fields = this.fields
      if (this.existingFieldId !== null) {
        fields = fields.filter((f) => f.id !== this.existingFieldId)
      }
      return !fields.map((f) => f.name).includes(param?.trim())
    },
    mustNotClashWithReservedName(param) {
      return !RESERVED_BASEROW_FIELD_NAMES.includes(param?.trim())
    },
    getFormComponent(type) {
      return this.$registry.get('field', type).getFormComponent()
    },
    showFieldTypesDropdown(target) {
      this.$refs.fieldTypesDropdown.show(target)
    },
    handleSuggestedFieldName(event) {
      if (this.isNameFieldEmptyOrPrefilled) {
        this.isPrefilledWithSuggestedFieldName = true
        const availableFieldName = this.getNextAvailableFieldName(event)
        this.values.name = availableFieldName
      }
    },
    getNextAvailableFieldName(baseName) {
      const excludeNames = this.fields.map((f) => f.name)
      return getNextAvailableNameInSequence(baseName, excludeNames)
    },
    handleKeydownEnter(event) {
      event.preventDefault()
      this.$emit('keydown-enter')
      this.submit()
    },
  },
}
</script>
