<template functional>
  <span v-if="props.column.additionalProps.userId === props.row.user_id">
    {{
      $options.methods.roleName(props.column.additionalProps.roles, props.row)
    }}
  </span>
  <a
    v-else
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
    {{
      $options.methods.roleName(props.column.additionalProps.roles, props.row)
    }}
    <i class="fas fa-chevron-down"></i>
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
