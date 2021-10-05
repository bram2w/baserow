<template>
  <div class="paginator">
    <div class="paginator__name">{{ $t('paginator.page') }}</div>
    <div class="paginator__group">
      <a
        class="paginator__button"
        :class="{
          'paginator__button--disabled': page === 1,
        }"
        @click="changePage(page - 1)"
      >
        <i class="fas fa-caret-left"></i>
      </a>
      <input
        v-model.number="textInputPage"
        class="input paginator__page-input"
        type="number"
        @keypress.enter="changePage(textInputPage)"
      />
      <div class="paginator__count">
        {{ $t('paginator.of', { pages: totalPages }) }}
      </div>
      <a
        class="paginator__button"
        :class="{
          'paginator__button--disabled': page === totalPages,
        }"
        @click="changePage(page + 1)"
      >
        <i class="fas fa-caret-right"></i>
      </a>
    </div>
  </div>
</template>
<script>
/**
 * Shows pagination buttons and the current page. Emits a `change-page` event when the
 * user attempts to change the page. If this event is successfully completed it is up
 * the parent component to update the provided page prop to show the new current page.
 */
export default {
  name: 'Paginator',
  props: {
    /**
     * The total number of pages available.
     */
    totalPages: {
      required: true,
      validator: (prop) => typeof prop === 'number' || prop === null,
    },
    /**
     * The currently selected page.
     */
    page: {
      required: true,
      type: Number,
    },
  },
  data() {
    return {
      textInputPage: 1,
    }
  },
  watch: {
    page(newPage) {
      this.textInputPage = newPage
    },
  },
  methods: {
    invalidNewPage(newPage) {
      return (
        typeof newPage !== 'number' ||
        (this.totalPages !== null &&
          this.totalPages !== 0 &&
          (newPage > this.totalPages || newPage < 1))
      )
    },
    changePage(newPage) {
      if (this.invalidNewPage(newPage)) {
        this.textInputPage = this.page
        return
      }
      this.$emit('change-page', newPage)
    },
  },
}
</script>

<i18n>
{
  "en": {
    "paginator": {
      "page": "page",
      "of": "of {pages}"
    }
  },
  "fr": {
    "paginator": {
      "page": "page",
      "of": "sur {pages}"
    }
  }
}
</i18n>
