<template>
  <div class="local-baserow-table-selector">
    <FormElement class="control local-baserow-table-selector__input">
      <label class="control__label control__label--small">
        {{ $t('localBaserowListRowsForm.databaseFieldLabel') }}
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
        {{ $t('localBaserowListRowsForm.tableFieldLabel') }}
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
    <FormInput
      class="local-baserow-table-selector__input"
      type="number"
      small-label
      :value="viewId"
      :label="$t('localBaserowListRowsForm.viewFieldLabel')"
      :placeholder="$t('localBaserowListRowsForm.viewFieldPlaceHolder')"
      :from-value="(value) => (value ? value : '')"
      :to-value="(value) => (value ? value : null)"
      @input="$emit('update:view-id', parseInt($event))"
    />
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
