<template>
  <form @submit.prevent>
    <FormGroup
      class="style-box-form__control margin-bottom-2"
      :label="label"
      small-label
      required
      :error="error"
    >
      <div
        v-if="borderIsAllowed || paddingIsAllowed"
        class="row margin-bottom-2"
        style="--gap: 6px"
      >
        <div v-if="borderIsAllowed" class="col col-4">
          <div class="margin-bottom-1">
            {{ $t('styleBoxForm.borderLabel') }}
          </div>
          <FormInput
            v-model="values.border_size"
            size="large"
            type="number"
            :min="0"
            :max="200"
            :error="error"
            @blur="$v.values.border_size.$touch()"
          ></FormInput>
        </div>
        <div v-if="paddingIsAllowed" class="col col-4">
          <div class="margin-bottom-1">
            {{ $t('styleBoxForm.paddingLabel') }}
          </div>
          <FormInput
            v-model="values.padding"
            size="large"
            type="number"
            :error="error"
            @blur="$v.values.padding.$touch()"
          ></FormInput>
        </div>
      </div>
      <ColorInputGroup
        v-if="borderIsAllowed"
        v-model="values.border_color"
        label-after
        class="margin-top-2"
        :label="$t('styleBoxForm.borderLabel')"
        :color-variables="colorVariables"
      />
    </FormGroup>
  </form>
</template>

<script>
import { required, integer, between } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'
import { themeToColorVariables } from '@baserow/modules/builder/utils/theme'

export default {
  name: 'StyleBoxForm',
  mixins: [form],
  inject: ['builder'],
  props: {
    label: {
      type: String,
      required: true,
    },
    value: {
      type: Object,
      required: true,
    },
    paddingIsAllowed: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    borderIsAllowed: {
      type: Boolean,
      required: false,
      default: () => false,
    },
  },
  data() {
    return {
      values: {
        padding: 0,
        border_color: 'border',
        border_size: 0,
      },
    }
  },
  computed: {
    colorVariables() {
      return themeToColorVariables(this.builder.theme)
    },
    /**
     * Returns only one error because we don't have the space to write one error per
     * field as the style fields are on the same line.
     */
    error() {
      return this.$v.values.padding.$error || this.$v.values.border_size.$error
    },
  },
  methods: {
    getDefaultValues() {
      return this.value
    },
    emitChange(newValues) {
      this.$emit('input', newValues)
    },
  },
  validations() {
    return {
      values: {
        padding: {
          required,
          integer,
          between: between(0, 200),
        },
        border_size: {
          required,
          integer,
          between: between(0, 200),
        },
      },
    }
  },
}
</script>
