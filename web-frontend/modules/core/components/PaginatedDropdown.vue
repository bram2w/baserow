<template>
  <div
    class="dropdown"
    :class="{
      'dropdown--floating': !showInput,
      'dropdown--disabled': disabled,
    }"
    :tabindex="realTabindex"
    @focusin="show()"
    @focusout="focusout($event)"
  >
    <a v-if="showInput" class="dropdown__selected" @click="show()">
      <template v-if="displayName !== null">
        {{ displayName }}
      </template>
      <template v-else>{{
        notSelectedText === null ? $t('action.makeChoice') : notSelectedText
      }}</template>
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
          tabindex="0"
          :placeholder="searchText === null ? $t('action.search') : searchText"
          @input="search"
        />
      </div>
      <ul
        ref="items"
        v-auto-overflow-scroll
        class="select__items"
        tabindex=""
        @scroll="scroll"
      >
        <DropdownItem
          v-if="addEmptyItem"
          :name="emptyItemDisplayName"
          :value="null"
        ></DropdownItem>
        <DropdownItem
          v-for="result in results"
          :key="result[idName]"
          :name="result[valueName]"
          :value="result[idName]"
        ></DropdownItem>
        <div v-if="loading" class="select__items-loading"></div>
      </ul>
    </div>
  </div>
</template>

<script>
import paginatedDropdown from '@baserow/modules/core/mixins/paginatedDropdown'

export default {
  name: 'PaginatedDropdown',
  mixins: [paginatedDropdown],
  props: {
    fetchPage: {
      type: Function,
      required: true,
    },
  },
}
</script>
