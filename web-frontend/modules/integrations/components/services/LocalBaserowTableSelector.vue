<template>
  <div class="local-baserow-table-selector">
    <FormElement class="control local-baserow-table-selector__input">
      <label class="control__label control__label--small">
        {{ $t('localBaserowTableSelector.databaseFieldLabel') }}
      </label>
      <Dropdown v-model="databaseSelectedId" :show-search="false">
        <DropdownItem
          v-for="database in databases"
          :key="database.id"
          :name="database.name"
          :value="database.id"
        >
          {{ database.name }}
        </DropdownItem>
      </Dropdown>
    </FormElement>
    <FormElement class="control local-baserow-table-selector__input">
      <label class="control__label control__label--small">
        {{ $t('localBaserowTableSelector.tableFieldLabel') }}
      </label>
      <Dropdown
        :value="value"
        :show-search="false"
        :disabled="databaseSelectedId === null"
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
    </FormElement>
    <FormElement class="control local-baserow-table-selector__input">
      <label class="control__label control__label--small">
        {{ $t('localBaserowTableSelector.viewFieldLabel') }}
      </label>
      <Dropdown
        :value="viewId"
        :show-search="false"
        :disabled="value === null"
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
    </FormElement>
  </div>
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
