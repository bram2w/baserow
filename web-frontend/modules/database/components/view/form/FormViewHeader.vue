<template>
  <ul v-if="!tableLoading" class="header__filter header__filter--full-width">
    <li class="header__filter-item">
      <a
        :href="formUrl"
        target="_blank"
        rel="noopener"
        class="header__filter-link"
      >
        <i class="header__filter-icon fas fa-eye"></i>
        <span class="header__filter-name">Preview</span>
      </a>
    </li>
  </ul>
</template>

<script>
import { mapState } from 'vuex'

import formViewHelpers from '@baserow/modules/database/mixins/formViewHelpers'

export default {
  name: 'FormViewHeader',
  mixins: [formViewHelpers],
  props: {
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    formUrl() {
      return (
        this.$env.PUBLIC_WEB_FRONTEND_URL +
        this.$nuxt.$router.resolve({
          name: this.$registry.get('view', this.view.type).getPublicRoute(),
          params: { slug: this.view.slug },
        }).href
      )
    },
    ...mapState({
      tableLoading: (state) => state.table.loading,
    }),
  },
}
</script>
