<template>
  <form class="context-form" @submit.prevent="submit">
    <div class="control">
      <div class="control-elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input-error': $v.values.name.$error }"
          type="text"
          class="input"
          placeholder="Name"
          @blur="$v.values.name.$touch()"
        />
        <div v-if="$v.values.name.$error" class="error">
          This field is required.
        </div>
      </div>
    </div>
    <div class="control">
      <div class="control-elements">
        <Dropdown
          v-model="values.type"
          :class="{ 'dropdown-error': $v.values.type.$error }"
          @hide="$v.values.type.$touch()"
        >
          <DropdownItem
            v-for="(fieldType, type) in fieldTypes"
            :key="type"
            :icon="fieldType.iconClass"
            :name="fieldType.name"
            :value="fieldType.type"
          ></DropdownItem>
        </Dropdown>
        <div v-if="$v.values.type.$error" class="error">
          This field is required.
        </div>
      </div>
    </div>
    <template v-if="!!values.type">
      <component
        :is="getFormComponent(values.type)"
        ref="childForm"
        :default-values="defaultValues"
      />
    </template>
    <slot></slot>
  </form>
</template>

<script>
import { mapState } from 'vuex'
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

// @TODO focus form on open
export default {
  name: 'FieldForm',
  mixins: [form],
  data() {
    return {
      allowedValues: ['name', 'type'],
      values: {
        name: '',
        type: ''
      }
    }
  },
  computed: {
    ...mapState({
      fieldTypes: state => state.field.types
    })
  },
  validations: {
    values: {
      name: { required },
      type: { required }
    }
  },
  methods: {
    getFormComponent(type) {
      return this.$store.getters['field/getType'](type).getFormComponent()
    }
  }
}
</script>
