<template>
  <a
    class="filters__value-link-row"
    :class="{ 'filters__value-link-row--disabled': readOnly }"
    @click.prevent="!readOnly && $refs.selectModal.show()"
  >
    <template v-if="valid">
      {{ name || `unnamed row ${filter.value}` }}
    </template>
    <div v-else class="filters__value-link-row-choose">Choose row</div>
    <SelectRowModal
      v-if="!readOnly"
      ref="selectModal"
      :table-id="field.link_row_table"
      @selected="setValue"
    ></SelectRowModal>
  </a>
</template>

<script>
import { isNumeric } from '@baserow/modules/core/utils/string'
import SelectRowModal from '@baserow/modules/database/components/row/SelectRowModal'
import viewFilter from '@baserow/modules/database/mixins/viewFilter'

export default {
  name: 'ViewFilterTypeLinkRow',
  components: { SelectRowModal },
  mixins: [viewFilter],
  data() {
    return {
      name: '',
    }
  },
  computed: {
    valid() {
      return this.isValidValue(this.filter.value)
    },
  },
  watch: {
    'filter.preload_values'(value) {
      this.setNameFromPreloadValues(value)
    },
  },
  mounted() {
    this.setNameFromPreloadValues(this.filter.preload_values)
  },
  methods: {
    setNameFromRow(row, primary) {
      this.name = this.$registry
        .get('field', primary.type)
        .toHumanReadableString(primary, row[`field_${primary.id}`])
    },
    setNameFromPreloadValues(values) {
      if (Object.prototype.hasOwnProperty.call(values, 'display_name')) {
        this.name = values.display_name
      }
    },
    isValidValue() {
      if (!isNumeric(this.filter.value)) {
        return false
      }

      return true
    },
    setValue({ row, primary }) {
      this.setNameFromRow(row, primary)
      this.$emit('input', row.id.toString())
    },
  },
}
</script>
