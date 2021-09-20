<template>
  <Context
    :class="{ 'context--loading-overlay': view._.loading }"
    @shown="focus"
  >
    <form class="context__form" @submit.prevent="searchIfChanged">
      <div class="control margin-bottom-1">
        <div class="control__elements">
          <div
            class="input__with-icon input__with-icon--left"
            :class="{ 'input__with-icon--loading': loading }"
          >
            <input
              ref="activeSearchTermInput"
              v-model="activeSearchTerm"
              type="text"
              :placeholder="$t('viewSearchContext.searchInRows')"
              class="input"
              @keyup="searchIfChanged"
            />
            <i class="fas fa-search"></i>
          </div>
        </div>
      </div>
      <div class="control control--align-right margin-bottom-0">
        <SwitchInput
          v-model="hideRowsNotMatchingSearch"
          @input="searchIfChanged"
        >
          {{ $t('viewSearchContext.hideNotMatching') }}
        </SwitchInput>
      </div>
    </form>
  </Context>
</template>

<script>
import debounce from 'lodash/debounce'

import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'ViewSearchContext',
  mixins: [context],
  props: {
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    primary: {
      type: Object,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      activeSearchTerm: '',
      lastSearch: '',
      hideRowsNotMatchingSearch: true,
      lastHide: true,
      loading: false,
    }
  },
  methods: {
    focus() {
      this.$nextTick(function () {
        this.$refs.activeSearchTermInput.focus()
      })
    },
    searchIfChanged() {
      this.$emit('search-changed', this.activeSearchTerm)
      if (
        this.lastSearch === this.activeSearchTerm &&
        this.lastHide === this.hideRowsNotMatchingSearch
      ) {
        return
      }

      this.search()

      this.lastSearch = this.activeSearchTerm
      this.lastHide = this.hideRowsNotMatchingSearch
    },
    search() {
      this.loading = true

      // When the user toggles from hiding rows to not hiding rows we still
      // need to refresh as we need to fetch the un-searched rows from the server first.
      if (this.hideRowsNotMatchingSearch || this.lastHide) {
        // noinspection JSValidateTypes
        this.debouncedServerSearchRefresh()
      } else {
        // noinspection JSValidateTypes
        this.debouncedClientSideSearchRefresh()
      }
    },
    debouncedServerSearchRefresh: debounce(async function () {
      await this.$store.dispatch(this.storePrefix + 'view/grid/updateSearch', {
        activeSearchTerm: this.activeSearchTerm,
        hideRowsNotMatchingSearch: this.hideRowsNotMatchingSearch,
        // The refresh event we fire below will cause the table to refresh it state from
        // the server using the newly set search terms.
        refreshMatchesOnClient: false,
        fields: this.fields,
        primary: this.primary,
      })
      this.$emit('refresh', {
        callback: this.finishedLoading,
      })
    }, 400),
    // Debounce even the client side only refreshes as otherwise spamming the keyboard
    // can cause many refreshes to queue up quickly bogging down the UI.
    debouncedClientSideSearchRefresh: debounce(async function () {
      await this.$store.dispatch(this.storePrefix + 'view/grid/updateSearch', {
        activeSearchTerm: this.activeSearchTerm,
        hideRowsNotMatchingSearch: this.hideRowsNotMatchingSearch,
        refreshMatchesOnClient: true,
        fields: this.fields,
        primary: this.primary,
      })
      this.finishedLoading()
    }, 10),
    finishedLoading() {
      this.loading = false
    },
  },
}
</script>

<i18n>
{
  "en": {
    "viewSearchContext": {
      "searchInRows": "Search in all rows",
      "hideNotMatching": "hide not matching rows"
    }
  },
  "fr": {
    "viewSearchContext": {
      "searchInRows": "Chercher dans toute la table",
      "hideNotMatching": "cacher les lignes sans résultat"
    }
  }
}
</i18n>
