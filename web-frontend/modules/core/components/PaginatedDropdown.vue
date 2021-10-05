<template>
  <div
    class="dropdown"
    :class="{
      'dropdown--floating': !showInput,
      'dropdown--disabled': disabled,
    }"
  >
    <a v-if="showInput" class="dropdown__selected" @click="show()">
      <template v-if="displayName !== null">
        {{ displayName }}
      </template>
      <template v-else>{{ $t('action.makeChoice') }}</template>
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
          @input="search"
        />
      </div>
      <ul
        ref="items"
        v-auto-overflow-scroll
        class="select__items"
        @scroll="scroll"
      >
        <DropdownItem :name="''" :value="null"></DropdownItem>
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
import debounce from 'lodash/debounce'

import dropdown from '@baserow/modules/core/mixins/dropdown'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'Dropdown',
  mixins: [dropdown],
  props: {
    fetchPage: {
      type: Function,
      required: true,
    },
    // The attribute name that contains the identifier in the fetched results.
    idName: {
      type: String,
      required: false,
      default: 'id',
    },
    // The attribute name that contains the display value in the fetched results.
    valueName: {
      type: String,
      required: false,
      default: 'value',
    },
    fetchOnOpen: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      fetched: false,
      displayName: null,
      count: 0,
      page: 1,
      loading: false,
      results: [],
    }
  },
  /**
   * When the component is first created, we immediately fetch the first page.
   */
  async created() {
    if (!this.fetchOnOpen) {
      this.fetched = true
      this.results = await this.fetch(this.page, this.query)
    }
  },
  methods: {
    /**
     * Because the dropdown items could be destroyed in case of a search and because we
     * don't need reactivity, we store a copy of the name as display name as soon as it
     * has changed.
     */
    select(value) {
      dropdown.methods.select.call(this, value)
      this.displayName = this.getSelectedProperty(value, 'name')
    },
    async fetch(page = 1, search = null) {
      this.page = page
      this.loading = true

      try {
        const { data } = await this.fetchPage(page, search)
        this.count = data.count
        this.loading = false
        return data.results
      } catch (e) {
        this.loading = false
        notifyIf(e)
        return []
      }
    },
    /**
     * Because the results change when you search, we need to reset the state before
     * searching. Otherwise there could be conflicting results.
     */
    search() {
      this.results = []
      this.page = 1
      this.count = 0
      this.loading = true
      this._search()
    },
    /**
     * Small debounce when searching to prevent a lot of requests to the backend.
     */
    _search: debounce(async function () {
      this.results = await this.fetch(this.page, this.query)
    }, 400),
    /**
     * When the user scrolls in the results, we can check if the user is near the end
     * and if so a new page will be loaded.
     */
    async scroll() {
      const items = this.$refs.items
      const max = items.scrollHeight - items.clientHeight

      if (
        !this.loading &&
        this.results.length < this.count &&
        items.scrollTop > max - 30
      ) {
        this.results.push(...(await this.fetch(this.page + 1, this.query)))
      }
    },
    async show(...args) {
      dropdown.methods.show.call(this, ...args)
      if (!this.fetched) {
        this.fetched = true
        this.results = await this.fetch(this.page, this.query)
      }
    },
    /**
     * Normally, when the dropdown hides, the search is reset, but in this case we
     * don't want to do that because otherwise results are refreshed everytime the
     * user closes dropdown.
     */
    hide() {
      this.open = false
      this.$emit('hide')
      document.body.removeEventListener('click', this.$el.clickOutsideEvent)
      document.body.removeEventListener('keydown', this.$el.keydownEvent)
    },
  },
}
</script>
