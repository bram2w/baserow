<template>
  <div>
    <div class="row">
      <div class="col col-4">
        <div class="control">
          <label class="control__label">Column separator</label>
          <div class="control__elements">
            <Dropdown v-model="values.csv_column_separator" :disabled="loading">
              <DropdownItem name="," value=","></DropdownItem>
              <DropdownItem name=";" value=";"></DropdownItem>
              <DropdownItem name="|" value="|"></DropdownItem>
              <DropdownItem name="<tab>" value="tab"></DropdownItem>
              <DropdownItem
                name="record separator (30)"
                value="record_separator"
              ></DropdownItem>
              <DropdownItem
                name="unit separator (31)"
                value="unit_separator"
              ></DropdownItem>
            </Dropdown>
          </div>
        </div>
      </div>
      <div class="col col-8">
        <div class="control">
          <label class="control__label">Encoding</label>
          <div class="control__elements">
            <CharsetDropdown
              v-model="values.export_charset"
              :disabled="loading"
            >
            </CharsetDropdown>
          </div>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col col-6">
        <div class="control">
          <label class="control__label">First row is header</label>
          <div class="control__elements">
            <Checkbox v-model="values.csv_first_row_header" :disabled="loading"
              >yes</Checkbox
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// Please keep csvColumnSeparator values in sync with
// src/baserow/contrib/database/api/export/serializers.py:SUPPORTED_CSV_COLUMN_SEPARATORS
import CharsetDropdown from '@baserow/modules/core/components/helpers/CharsetDropdown'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'TableCSVExporter',
  components: { CharsetDropdown },
  mixins: [form],
  props: {
    loading: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      values: {
        csv_first_row_header: true,
        export_charset: 'utf-8',
        csv_column_separator: ',',
      },
    }
  },
}
</script>
