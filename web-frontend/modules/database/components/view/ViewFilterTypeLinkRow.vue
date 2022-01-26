<template>
  <PaginatedDropdown
    v-if="readOnly && view"
    :fetch-page="fetchPage"
    :value="filter.value"
    :fetch-on-open="true"
    :disabled="disabled"
    class="filters__value-dropdown dropdown--tiny"
    @input="$emit('input', $event)"
  ></PaginatedDropdown>
  <a
    v-else
    class="filters__value-link-row"
    :class="{ 'filters__value-link-row--disabled': disabled }"
    @click.prevent="!disabled && $refs.selectModal.show()"
  >
    <template v-if="valid">
      {{ name || $t('viewFilterTypeLinkRow.unnamed', { value: filter.value }) }}
    </template>
    <div v-else class="filters__value-link-row-choose">
      {{ $t('viewFilterTypeLinkRow.choose') }}
    </div>
    <SelectRowModal
      v-if="!disabled"
      ref="selectModal"
      :table-id="field.link_row_table"
      @selected="setValue"
    ></SelectRowModal>
  </a>
</template>

<script>
import { isNumeric } from '@baserow/modules/core/utils/string'
import PaginatedDropdown from '@baserow/modules/core/components/PaginatedDropdown'
import SelectRowModal from '@baserow/modules/database/components/row/SelectRowModal'
import viewFilter from '@baserow/modules/database/mixins/viewFilter'
import ViewService from '@baserow/modules/database/services/view'

export default {
  name: 'ViewFilterTypeLinkRow',
  components: { PaginatedDropdown, SelectRowModal },
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
    fetchPage(page, search) {
      return ViewService(this.$client).linkRowFieldLookup(
        this.view.id,
        this.field.id,
        page,
        search
      )
    },
  },
}
</script>
