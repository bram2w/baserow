<template>
  <div>
    <header class="layout-col-3-1 header">
      <ul class="header-filter">
        <li class="header-filter-item">&nbsp;</li>
      </ul>
      <ul class="header-info">
        <li>{{ selectedApplication.name }}</li>
        <li>@TODO table name</li>
      </ul>
    </header>
  </div>
</template>

<script>
import { mapState } from 'vuex'

import application from '@/mixins/application'

export default {
  layout: 'app',
  mixins: [application],
  computed: {
    ...mapState({
      selectedApplication: state => state.application.selected
    })
  }
}
</script>
