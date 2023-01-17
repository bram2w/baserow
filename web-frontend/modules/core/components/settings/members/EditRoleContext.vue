<template>
  <Context>
    <template v-if="Object.keys(subject).length > 0">
      <div class="context__menu-title">
        <div class="edit-role-context__header">
          <div>
            {{ $t('membersSettings.membersTable.columns.role') }}
          </div>
          <div v-if="atLeastOneBillableRole">
            <i class="fas fa-fw fa-book"></i>
            <a
              href="https://baserow.io/user-docs/subscriptions-overview#who-is-considered-a-user-for-billing-purposes"
              target="_blank"
            >
              {{ $t('editRoleContext.billableRolesLink') }}
            </a>
          </div>
        </div>
      </div>
      <ul class="context__menu context__menu--can-be-active">
        <li v-for="role in roles" :key="role.uid">
          <a
            :class="{ active: subject[roleValueColumn] === role.uid }"
            @click="roleUpdate(role.uid, subject)"
          >
            <div class="edit-role-context__role-name">
              {{ role.name }}
              <Badge
                v-if="!role.isBillable && atLeastOneBillableRole"
                primary
                class="margin-left-1"
                >{{ $t('common.free') }}
              </Badge>
            </div>
            <div v-if="role.description" class="context__menu-item-description">
              {{ role.description }}
            </div>
          </a>
        </li>
        <li>
          <a
            v-if="allowRemovingRole"
            class="context__menu-item--delete"
            @click="$emit('delete')"
            >{{ $t('action.remove') }}</a
          >
        </li>
      </ul>
    </template>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'EditRoleContext',
  mixins: [context],
  props: {
    subject: {
      required: true,
      type: Object,
    },
    roles: {
      required: true,
      type: Array,
    },
    roleValueColumn: {
      type: String,
      required: false,
      default: 'permissions',
    },
    allowRemovingRole: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    atLeastOneBillableRole() {
      return this.roles.some((role) => role.isBillable)
    },
  },
  methods: {
    roleUpdate(roleNew, subject) {
      if (subject[this.roleValueColumn] === roleNew) {
        return
      }

      this.$emit('update-role', { uid: roleNew, subject })
      this.hide()
    },
  },
}
</script>
