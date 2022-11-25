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
          type: $t(`selectSubjectsListFooter.types.${type}`),
        })
      }}
    </a>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import RoleSelector from '@baserow_enterprise/components/member-roles/RoleSelector'
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
    type: {
      type: String,
      validator: (type) => type === 'teams' || 'members',
      default: 'members',
    },
  },
  data() {
    return {
      roleSelected: {},
    }
  },
  computed: {
    ...mapGetters({ group: 'group/getSelected' }),
    roles() {
      return this.group ? this.group._.roles : []
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
