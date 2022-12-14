<template>
  <Context>
    <template v-if="Object.keys(team).length > 0">
      <ul class="context__menu">
        <li
          v-if="$hasPermission('enterprise.teams.team.update', group, group.id)"
        >
          <a @click="handleEditClick(team)">
            <i class="context__menu-icon fas fa-fw fa-pen"></i>
            {{ $t('editTeamContext.edit') }}
          </a>
        </li>
        <li
          v-if="$hasPermission('enterprise.teams.team.delete', group, group.id)"
        >
          <a
            :class="{
              'context__menu-item--loading': removeLoading,
            }"
            class="color-error"
            @click.prevent="remove(team)"
          >
            <i class="context__menu-icon fas fa-fw fa-trash"></i>
            {{ $t('editTeamContext.remove') }}
          </a>
        </li>
      </ul>
    </template>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import { notifyIf } from '@baserow/modules/core/utils/error'
import TeamService from '@baserow_enterprise/services/team'

export default {
  name: 'EditTeamContext',
  mixins: [context],
  props: {
    group: {
      required: true,
      type: Object,
    },
    team: {
      required: true,
      type: Object,
    },
  },
  data() {
    return {
      removeLoading: false,
    }
  },
  methods: {
    handleEditClick(team) {
      this.$emit('edit', team)
      this.hide()
    },
    async remove(team) {
      if (this.removeLoading) {
        return
      }

      this.removeLoading = true

      try {
        await TeamService(this.$client).delete(team.id)
        this.$emit('deleted', team.id)
        this.hide()
      } catch (error) {
        notifyIf(error)
      } finally {
        this.removeLoading = false
      }
    },
  },
}
</script>
