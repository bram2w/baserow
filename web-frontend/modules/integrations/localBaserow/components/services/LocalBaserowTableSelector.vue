<template>
  <FormRow>
    <FormGroup
      :label="$t('localBaserowTableSelector.databaseFieldLabel')"
      small-label
      required
    >
      <Dropdown
        v-model="databaseSelectedId"
        :show-search="false"
        fixed-items
        :small="smallDropdowns"
      >
        <DropdownItem
          v-for="database in databases"
          :key="database.id"
          :name="database.name"
          :value="database.id"
        >
          {{ database.name }}
        </DropdownItem>
      </Dropdown>
    </FormGroup>

    <FormGroup
      :label="$t('localBaserowTableSelector.tableFieldLabel')"
      small-label
      required
    >
      <Dropdown
        :value="value"
        :show-search="false"
        :disabled="databaseSelectedId === null"
        fixed-items
        :small="smallDropdowns"
        @input="$emit('input', $event)"
      >
        <DropdownItem
          v-for="table in tables"
          :key="table.id"
          :name="table.name"
          :value="table.id"
        >
          {{ table.name }}
        </DropdownItem>
      </Dropdown>
    </FormGroup>
    <FormGroup
      v-if="displayViewDropdown"
      :label="$t('localBaserowTableSelector.viewFieldLabel')"
      small-label
      required
    >
      <Dropdown
        :value="viewId"
        :show-search="false"
        :disabled="value === null"
        fixed-items
        :small="smallDropdowns"
        @input="$emit('update:view-id', $event)"
      >
        <DropdownItem
          :name="$t('localBaserowTableSelector.chooseNoView')"
          :value="null"
          >{{ $t('localBaserowTableSelector.chooseNoView') }}</DropdownItem
        >
        <DropdownItem
          v-for="view in views"
          :key="view.id"
          :name="view.name"
          :value="view.id"
        >
          {{ view.name }}
        </DropdownItem>
      </Dropdown>
    </FormGroup>
  </FormRow>
</template>

<script>
export default {
  name: 'LocalBaserowTableSelector',
  props: {
    value: {
      type: Number,
      required: false,
      default: null,
    },
    viewId: {
      type: Number,
      required: false,
      default: null,
    },
    databases: {
      type: Array,
      required: true,
    },
    displayViewDropdown: {
      type: Boolean,
      default: true,
    },
    dropdownSizes: {
      type: String,
      required: false,
      validator: function (value) {
        return ['small', 'large'].includes(value)
      },
      default: 'small',
    },
  },
  data() {
    return {
      databaseSelectedId: null,
    }
  },
  computed: {
    databaseSelected() {
      return this.databases.find(
        (database) => database.id === this.databaseSelectedId
      )
    },
    tables() {
      return this.databaseSelected?.tables || []
    },
    views() {
      return (
        this.databaseSelected?.views.filter(
          (view) => view.table_id === this.value
        ) || []
      )
    },
    smallDropdowns() {
      return this.dropdownSizes === 'small'
    },
  },
  watch: {
    value: {
      handler(tableId) {
        if (tableId !== null) {
          const databaseOfTableId = this.databases.find((database) =>
            database.tables.some((table) => table.id === tableId)
          )
          if (databaseOfTableId) {
            this.databaseSelectedId = databaseOfTableId.id
          }
        }
      },
      immediate: true,
    },
  },
}
</script>
