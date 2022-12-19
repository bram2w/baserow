<template>
  <div
    class="select-list-footer"
    :class="{ 'select-list-footer--single': !showRoleSelector }"
  >
    <div v-if="showRoleSelector">
      <RoleSelector v-model="roleSelected" :roles="roles" />
    </div>
    <a
      class="button"
      :class="{ disabled: !inviteEnabled }"
      @click="inviteEnabled ? $emit('invite', roleSelected) : null"
      >{{
        $t('selectSubjectsListFooter.invite', {
          count,
          type: subjectTypeLabel,
        })
      }}
    </a>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import RoleSelector from '@baserow_enterprise/components/member-roles/RoleSelector'
import { filterRoles } from '@baserow_enterprise/utils/roles'

export default {
  name: 'SelectSubjectsListFooter',
  components: { RoleSelector },
  props: {
    showRoleSelector: {
      type: Boolean,
      default: false,
    },
    count: {
      type: Number,
      required: true,
    },
    subjectType: {
      type: String,
      required: true,
    },
    scopeType: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      roleSelected: {},
    }
  },
  computed: {
    ...mapGetters({ group: 'group/getSelected' }),
    subjectTypeLabel() {
      switch (this.subjectType) {
        case 'auth.User':
          return this.$t('selectSubjectsListFooter.types.members')
        case 'baserow_enterprise.Team':
          return this.$t('selectSubjectsListFooter.types.teams')
        default:
          return ''
      }
    },
    roles() {
      return this.group
        ? filterRoles(this.group._.roles, {
            scopeType: this.scopeType,
            subjectType: this.subjectType,
          })
        : []
    },
    inviteEnabled() {
      return this.count !== 0
    },
  },
  mounted() {
    // Set a default selected role, the last role is usually the one with the least
    // access
    this.roleSelected =
      this.roles.length > 0 ? this.roles[this.roles.length - 1] : {}
  },
}
</script>
