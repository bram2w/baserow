<template>
  <form @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('name')" class="control">
      <label class="control__label">
        <i class="fas fa-font"></i>
        {{ $t('pageForm.nameLabel') }}
      </label>
      <input
        ref="name"
        v-model="values.name"
        type="text"
        class="input input--large"
        :class="{ 'input--error': fieldHasErrors('name') }"
        @focus.once="$event.target.select()"
        @blur="$v.values.name.$touch()"
      />
      <div
        v-if="$v.values.name.$dirty && !$v.values.name.required"
        class="error"
      >
        {{ $t('error.requiredField') }}
      </div>
      <div
        v-if="$v.values.name.$dirty && !$v.values.name.maxLength"
        class="error"
      >
        {{ $t('error.maxLength', { max: 255 }) }}
      </div>
      <div
        v-if="$v.values.name.$dirty && !$v.values.name.isUnique"
        class="error"
      >
        {{ $t('pageForm.errorNameNotUnique') }}
      </div>
    </FormElement>
    <slot></slot>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { maxLength, required } from 'vuelidate/lib/validators'
import { getNextAvailableNameInSequence } from '@baserow/modules/core/utils/string'

export default {
  name: 'PageForm',
  mixins: [form],
  props: {
    builder: {
      type: Object,
      required: true,
    },
    creation: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      allowedValues: ['name'],
      values: {
        name: null,
      },
    }
  },
  computed: {
    pageNames() {
      return this.builder.pages.map((page) => page.name)
    },
    defaultName() {
      const baseName = this.$t('pageForm.defaultName')
      return getNextAvailableNameInSequence(baseName, this.pageNames)
    },
  },
  created() {
    if (this.creation) {
      this.values.name = this.defaultName
    }
  },
  mounted() {
    if (this.creation) {
      this.$refs.name.focus()
    }
  },
  methods: {
    isNameUnique(name) {
      return !this.pageNames.includes(name)
    },
  },
  validations() {
    return {
      values: {
        name: {
          required,
          isUnique: this.isNameUnique,
          maxLength: maxLength(255),
        },
      },
    }
  },
}
</script>
