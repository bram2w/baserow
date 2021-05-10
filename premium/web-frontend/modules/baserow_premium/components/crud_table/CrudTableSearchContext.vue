<template>
  <Context @shown="focus">
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
              placeholder="Search usernames"
              class="input"
              @keyup="searchIfChanged"
            />
            <i class="fas fa-search"></i>
          </div>
        </div>
      </div>
    </form>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'CrudTableSearchContext',
  mixins: [context],
  props: {
    loading: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      activeSearchTerm: '',
      lastSearch: '',
    }
  },
  methods: {
    focus() {
      this.$nextTick(function () {
        this.$refs.activeSearchTermInput.focus()
      })
    },
    searchIfChanged() {
      if (this.lastSearch === this.activeSearchTerm) {
        return
      }

      this.$emit('search-changed', this.activeSearchTerm)

      this.lastSearch = this.activeSearchTerm
    },
  },
}
</script>
