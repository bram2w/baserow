<template>
  <div class="select-application">
    <template v-if="hasDatabases">
      <APIDocsSelectDatabaseGroup
        v-for="group in groups"
        :key="group.id"
        :group="group"
        :selected="selected"
      ></APIDocsSelectDatabaseGroup>
    </template>
    <p v-else>
      {{ $t('apiDocsSelectDatabase') }}
    </p>
  </div>
</template>

<script>
import { mapState } from 'vuex'

import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import APIDocsSelectDatabaseGroup from '@baserow/modules/database/components/docs/APIDocsSelectDatabaseGroup'

export default {
  name: 'APIDocsSelectDatabase',
  components: { APIDocsSelectDatabaseGroup },
  props: {
    selected: {
      type: Number,
      required: false,
      default: -1,
    },
  },
  computed: {
    hasDatabases() {
      const databaseType = DatabaseApplicationType.getType()
      return (
        this.$store.getters['application/getAll'].filter(
          (application) => application.type === databaseType
        ).length > 0
      )
    },
    ...mapState({
      groups: (state) => state.group.items,
    }),
  },
}
</script>
