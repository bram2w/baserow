<template>
  <FieldSingleSelectDropdown
    :value="copy"
    :options="field.select_options"
    :disabled="readOnly"
    class="dropdown--floating filters__value-dropdown dropdown--tiny"
    @input="input"
  ></FieldSingleSelectDropdown>
</template>

<script>
import FieldSingleSelectDropdown from '@baserow/modules/database/components/field/FieldSingleSelectDropdown'

export default {
  name: 'ViewFilterTypeSelectOptions',
  components: { FieldSingleSelectDropdown },
  props: {
    value: {
      type: String,
      required: true,
    },
    fieldId: {
      type: Number,
      required: true,
    },
    primary: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    copy() {
      const value = this.value
      return value === '' ? null : parseInt(value) || null
    },
    field() {
      return this.primary.id === this.fieldId
        ? this.primary
        : this.fields.find((f) => f.id === this.fieldId)
    },
  },
  methods: {
    input(value) {
      value = value === null ? '' : value.toString()
      this.$emit('input', value)
    },
  },
}
</script>
