<template>
  <div
    class="dropdown"
    :class="{
      'dropdown--floating': !showInput,
      'dropdown--disabled': disabled,
    }"
    @contextmenu.stop
  >
    <a
      v-if="showInput"
      class="field-single-select__dropdown-selected dropdown__selected"
      @click="show()"
    >
      <div
        v-if="hasValue()"
        class="field-single-select__dropdown-option"
        :class="'background-color--' + selectedColor"
      >
        {{ selectedName }}
      </div>
      <i v-if="!disabled" class="dropdown__toggle-icon fas fa-caret-down"></i>
    </a>
    <div class="dropdown__items" :class="{ hidden: !open }">
      <div v-if="showSearch" class="select__search">
        <i class="select__search-icon fas fa-search"></i>
        <input
          ref="search"
          v-model="query"
          type="text"
          class="select__search-input"
          :placeholder="searchText"
          @keyup="search(query)"
        />
      </div>
      <ul ref="items" v-prevent-parent-scroll class="select__items">
        <FieldSingleSelectDropdownItem
          :name="''"
          :value="null"
          :color="''"
        ></FieldSingleSelectDropdownItem>
        <FieldSingleSelectDropdownItem
          v-for="option in options"
          :key="option.id"
          :name="option.value"
          :value="option.id"
          :color="option.color"
        ></FieldSingleSelectDropdownItem>
      </ul>
      <template v-if="canCreateOption">
        <div class="select__description">Option not found</div>
        <div class="select__footer">
          <a
            class="select__footer-button"
            :class="{ 'button--loading': createOptionLoading }"
            @click="createOption(query)"
          >
            <i class="fas fa-plus"></i>
            Create {{ query }}
          </a>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
import dropdown from '@baserow/modules/core/mixins/dropdown'
import FieldSingleSelectDropdownItem from '@baserow/modules/database/components/field/FieldSingleSelectDropdownItem'

export default {
  name: 'FieldSingleSelectDropdown',
  components: { FieldSingleSelectDropdownItem },
  mixins: [dropdown],
  props: {
    options: {
      type: Array,
      required: true,
    },
    allowCreateOption: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      createOptionLoading: false,
    }
  },
  computed: {
    canCreateOption() {
      return this.allowCreateOption && this.query !== '' && !this.hasItems
    },
    selectedColor() {
      return this.getSelectedProperty(this.value, 'color')
    },
  },
  methods: {
    forceRefreshSelectedValue() {
      this._computedWatchers.selectedColor.run()
      dropdown.methods.forceRefreshSelectedValue.call(this)
    },
    createOption(value) {
      if (this.createOptionLoading) {
        return
      }

      this.createOptionLoading = true
      const done = (success) => {
        this.createOptionLoading = false

        // If the option was created successfully whe have to find that option, select
        // it and hide the dropdown.
        if (success) {
          const option = this.options.find((o) => o.value === value)
          if (option !== undefined) {
            this.select(option.id)
          }
        }
      }
      this.$emit('create-option', { value, done })
    },
  },
}
</script>
