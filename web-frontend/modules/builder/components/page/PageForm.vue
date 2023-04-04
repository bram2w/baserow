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
    <FormElement :error="fieldHasErrors('path')" class="control">
      <label class="control__label">
        <i class="fas fa-font"></i>
        {{ $t('pageForm.pathLabel') }}
      </label>
      <input
        ref="path"
        v-model="values.path"
        type="text"
        class="input input--large"
        :class="{ 'input--error': fieldHasErrors('path') }"
        @input="hasPathBeenEdited = true"
        @focus.once="$event.target.select()"
        @blur="$v.values.path.$touch()"
      />
      <div
        v-if="$v.values.path.$dirty && !$v.values.path.required"
        class="error"
      >
        {{ $t('error.requiredField') }}
      </div>
      <div
        v-if="$v.values.path.$dirty && !$v.values.path.isUnique"
        class="error"
      >
        {{ $t('pageForm.errorPathNotUnique') }}
      </div>
      <div
        v-if="$v.values.path.$dirty && !$v.values.path.maxLength"
        class="error"
      >
        {{ $t('error.maxLength', { max: 255 }) }}
      </div>
      <div
        v-if="$v.values.path.$dirty && !$v.values.path.startingSlash"
        class="error"
      >
        {{ $t('pageForm.errorStartingSlash') }}
      </div>
      <div
        v-if="$v.values.path.$dirty && !$v.values.path.validPathCharacters"
        class="error"
      >
        {{ $t('pageForm.errorValidPathCharacters') }}
      </div>
    </FormElement>
    <slot></slot>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { maxLength, required } from 'vuelidate/lib/validators'
import {
  getNextAvailableNameInSequence,
  slugify,
} from '@baserow/modules/core/utils/string'
import { VALID_PATH_CHARACTERS } from '@baserow/modules/builder/enums'

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
      allowedValues: ['name', 'path'],
      values: {
        name: '',
        path: '',
      },
      hasPathBeenEdited: false,
    }
  },
  computed: {
    pageNames() {
      return this.builder.pages.map((page) => page.name)
    },
    pagePaths() {
      return this.builder.pages.map((page) => page.path)
    },
    defaultName() {
      const baseName = this.$t('pageForm.defaultName')
      return getNextAvailableNameInSequence(baseName, this.pageNames)
    },
  },
  watch: {
    'values.name': {
      handler(value) {
        if (!this.hasPathBeenEdited && this.creation) {
          this.values.path = `/${slugify(value)}`
        }
      },
      immediate: true,
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
    isPathUnique(path) {
      return !this.pagePaths.includes(path)
    },
    pathStartsWithSlash(path) {
      return path[0] === '/'
    },
    pathHasValidCharacters(path) {
      return !path
        .split('')
        .some((letter) => !VALID_PATH_CHARACTERS.includes(letter))
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
        path: {
          required,
          isUnique: this.isPathUnique,
          maxLength: maxLength(255),
          startingSlash: this.pathStartsWithSlash,
          validPathCharacters: this.pathHasValidCharacters,
        },
      },
    }
  },
}
</script>
