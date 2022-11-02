<template>
  <form @submit.prevent="doSearch(headerSearchTerm, true)">
    <div
      class="input__with-icon input__with-icon--left"
      :class="{ 'input__with-icon--loading': loading }"
    >
      <input
        v-model="headerSearchTerm"
        type="text"
        :placeholder="$t('crudTableSearch.search')"
        class="input input--large"
        @keyup="searchIfChanged(headerSearchTerm, false)"
      />
      <i class="fas fa-search"></i>
    </div>
  </form>
</template>

<script>
import debounce from 'lodash/debounce'

/**
 * Will emit a `search-changed` event with the event object being the string of the
 * users search term. Takes a `loading` prop which will cause the search to display in
 * a loading state, it is upto the parent to set this when reacting to the
 * `searched-changed` event.
 *
 * This event is debounced internally so it will only be emitted after the user has
 * stopped typing for a short period of time, this way the component reacting to search
 * will not be spammed by an event for every single key press.
 */
export default {
  name: 'CrudTableSearch',
  props: {
    loading: {
      type: Boolean,
      required: true,
    },
  },
  data: () => {
    return {
      lastSearch: '',
      headerSearchTerm: '',
      searchDebounce: null,
    }
  },
  methods: {
    doSearch(query, immediate) {
      const search = () => {
        this.$emit('search-changed', query)
      }
      if (this.searchDebounce) {
        this.searchDebounce.cancel()
      }
      if (immediate) {
        search()
      } else {
        this.searchDebounce = debounce(search, 400)
        this.searchDebounce()
      }
    },
    searchIfChanged(query, immediate = false) {
      if (this.lastSearch === query) {
        return
      }

      this.lastSearch = query
      this.doSearch(query, immediate)
    },
  },
}
</script>
