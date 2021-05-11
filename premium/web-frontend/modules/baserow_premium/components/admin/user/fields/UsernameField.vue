<template functional>
  <div class="user-admin-username" :class="[data.staticClass, data.class]">
    <div class="user-admin-username__initials">
      {{ $options.methods.firstTwoInitials(props.row.name) }}
    </div>
    <div class="user-admin-username__name" :title="props.row.username">
      {{ props.row.username }}
    </div>
    <i
      v-if="props.row.is_staff"
      v-tooltip="'is staff'"
      class="user-admin-username__icon fas fa-users"
    ></i>
    <a
      class="user-admin-username__menu"
      @click.prevent="
        listeners['edit-user'] &&
          listeners['edit-user']({
            user: props.row,
            target: $event.currentTarget,
            time: Date.now(),
          })
      "
    >
      <i class="fas fa-ellipsis-h"></i>
    </a>
  </div>
</template>

<script>
export default {
  name: 'UsernameField',
  functional: true,
  props: {
    row: {
      required: true,
      type: Object,
    },
  },
  methods: {
    firstTwoInitials(name) {
      return name
        .split(' ')
        .map((s) => s.slice(0, 1))
        .join('')
        .slice(0, 2)
        .toUpperCase()
    },
  },
}
</script>
