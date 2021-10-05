<template>
  <form class="context__form" @submit.prevent="submit">
    <div class="control">
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': $v.values.name.$error }"
          type="text"
          class="input"
          :placeholder="$t('fieldForm.name')"
          @blur="$v.values.name.$touch()"
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
    </div>
    <div class="control">
      <div class="control__elements">
        <Dropdown
          v-model="values.type"
          :class="{ 'dropdown--error': $v.values.type.$error }"
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
        :default-values="defaultValues"
      />
    </template>
    <slot></slot>
  </form>
</template>

<script>
import { required, maxLength } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import { mapGetters } from 'vuex'
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
    primary: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      allowedValues: ['name', 'type'],
      values: {
        name: '',
        type: '',
      },
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
      fields: 'field/getAllWithPrimary',
    }),
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
      return !fields.map((f) => f.name).includes(param.trim())
    },
    mustNotClashWithReservedName(param) {
      return !RESERVED_BASEROW_FIELD_NAMES.includes(param.trim())
    },
    getFormComponent(type) {
      return this.$registry.get('field', type).getFormComponent()
    },
  },
}
</script>

<i18n>
{
  "en": {
    "fieldForm":{
      "name": "Name",
      "fieldAlreadyExists": "A field with this name already exists.",
      "nameNotAllowed": "This field name is not allowed.",
      "nameTooLong": "This field name is too long."
    }
  },
  "fr": {
    "fieldForm":{
      "name": "Nom",
      "fieldAlreadyExists": "Un champ avec ce nom existe déjà.",
      "nameNotAllowed": "Ce nom de champ n'est pas autorisé.",
      "nameTooLong": "Ce nom de champ est trop long."
    }
  }
}
</i18n>
