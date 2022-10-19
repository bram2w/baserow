<template>
  <div class="crudtable__dropdown-field">
    <Dropdown
      :disabled="disabled"
      :value="value"
      :show-search="false"
      @input="onInput"
    >
      <DropdownItem
        v-for="option in options"
        :key="option.value"
        :name="option.name"
        :value="option.value"
        :description="option.description"
      ></DropdownItem>
      <DropdownAction
        v-if="action"
        class="margin-top-1"
        :label="action.label"
        :color-class="action.colorClass"
        @click="$emit(action.onClickEventName, row)"
      >
      </DropdownAction>
    </Dropdown>
  </div>
</template>

<script>
import DropdownAction from '@baserow/modules/core/components/DropdownAction'
export default {
  name: 'DropdownField',
  components: { DropdownAction },
  props: {
    row: {
      required: true,
      type: Object,
    },
    column: {
      required: true,
      type: Object,
    },
  },
  computed: {
    value() {
      return this.row[this.column.key]
    },
    options() {
      return this.column.additionalProps?.options || []
    },
    action() {
      return this.column.additionalProps?.action || null
    },
    disabled() {
      if (typeof this.column.additionalProps?.disabled === 'function') {
        return this.column.additionalProps?.disabled(this.row)
      } else {
        return this.column.additionalProps?.disabled || false
      }
    },
    inputCallback() {
      return this.column.additionalProps?.inputCallback || null
    },
  },
  methods: {
    onInput(value) {
      const rowCopy = JSON.parse(JSON.stringify(this.row))
      rowCopy[this.column.key] = value

      if (this.inputCallback) {
        this.inputCallback(value, this.row)
      }

      this.$emit('row-update', rowCopy)
    },
  },
}
</script>
