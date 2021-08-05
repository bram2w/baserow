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
import viewFilter from '@baserow/modules/database/mixins/viewFilter'

export default {
  name: 'ViewFilterTypeSelectOptions',
  components: { FieldSingleSelectDropdown },
  mixins: [viewFilter],
  computed: {
    copy() {
      const value = this.filter.value
      return value === '' ? null : parseInt(value) || null
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
