<template>
  <div
    class="dropdown"
    :class="{
      'dropdown--floating': !showInput,
      'dropdown--disabled': disabled,
    }"
  >
    <a v-if="showInput" class="dropdown__selected" @click="show()">
      <template v-if="hasValue()">
        <i
          v-if="selectedIcon"
          class="dropdown__selected-icon fas"
          :class="'fa-' + selectedIcon"
        ></i>
        {{ selectedName }}
      </template>
      <template v-if="!hasValue()"> Make a choice </template>
      <i class="dropdown__toggle-icon fas fa-caret-down"></i>
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
      <ul ref="items" class="select__items">
        <slot></slot>
      </ul>
    </div>
  </div>
</template>

<script>
import dropdown from '@baserow/modules/core/mixins/dropdown'

export default {
  name: 'Dropdown',
  mixins: [dropdown],
}
</script>
