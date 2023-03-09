<template>
  <TeamsTable :group="group" />
</template>

<script>
import TeamsTable from '@baserow_enterprise/components/teams/TeamsTable'
import { ENTERPRISE_ACTION_SCOPES } from '@baserow_enterprise/undoRedoConstants'

export default {
  name: 'Teams',
  components: { TeamsTable },
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  mounted() {
    this.$store.dispatch(
      'undoRedo/updateCurrentScopeSet',
      ENTERPRISE_ACTION_SCOPES.teams_in_group(this.group.id)
    )
  },
  beforeDestroy() {
    this.$store.dispatch(
      'undoRedo/updateCurrentScopeSet',
      ENTERPRISE_ACTION_SCOPES.teams_in_group(null)
    )
  },
}
</script>
