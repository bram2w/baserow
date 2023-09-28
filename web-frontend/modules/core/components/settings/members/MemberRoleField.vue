<template functional>
  <span
    v-if="
      props.column.additionalProps.userId === props.row.user_id ||
      !parent.$hasPermission(
        'workspace_user.update',
        props.row,
        props.column.additionalProps.workspaceId
      )
    "
  >
    {{
      $options.methods.roleName(props.column.additionalProps.roles, props.row)
    }}
  </span>
  <a
    v-else
    class="member-role-field__link"
    @click.prevent="
      listeners['edit-role-context'] &&
        listeners['edit-role-context']({
          row: props.row,
          event: $event,
          target: $event.currentTarget,
          time: Date.now(),
        })
    "
  >
    <span
      >{{
        $options.methods.roleName(props.column.additionalProps.roles, props.row)
      }}
    </span>
    <i class="iconoir-nav-arrow-down"></i>
  </a>
</template>

<script>
export default {
  name: 'MemberRoleField',
  functional: true,
  methods: {
    roleName(roles, row) {
      const permissions = row.permissions === 'ADMIN' ? 'ADMIN' : 'MEMBER'
      const role = roles.find((r) => r.uid === permissions)
      return role?.name || ''
    },
  },
}
</script>
