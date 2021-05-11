<template>
  <div>
    <a
      ref="contextLink"
      class="crudtable__header-link"
      :class="{
        'active--primary': headerSearchTerm.length > 0,
      }"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 4)"
    >
      <i class="fas fa-search"></i>
      {{ headerSearchTerm }}
    </a>
    <CrudTableSearchContext
      ref="context"
      :loading="loading"
      @search-changed="searchChanged"
    ></CrudTableSearchContext>
  </div>
</template>

<script>
import debounce from 'lodash/debounce'
import CrudTableSearchContext from '@baserow_premium/components/crud_table/CrudTableSearchContext'

/**
 * A search component which shows a search modal when the user clicks on this
 * components search icon. Will emit a `search-changed` event with the event object
 * being the string of the users search term. Takes a `loading` prop which will cause
 * the search to display in a loading state, it is upto the parent to set this when
 * reacting to the `searched-changed` event.
 *
 * This event is debounced internally so it will only be emitted after the user has
 * stopped typing for a short period of time, this way the component reacting to search
 * will not be spammed by an event for every single key press.
 */
export default {
  name: 'CrudTableSearch',
  components: { CrudTableSearchContext },
  props: {
    loading: {
      type: Boolean,
      required: true,
    },
  },
  data: () => {
    return {
      headerSearchTerm: '',
    }
  },
  methods: {
    searchChanged(newSearch) {
      this.headerSearchTerm = newSearch
      this.debounceEmit()
    },
    debounceEmit: debounce(function () {
      this.$emit('search-changed', this.headerSearchTerm)
    }, 400),
  },
}
</script>
