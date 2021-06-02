<template functional>
  <div class="group-admin-name" :class="[data.staticClass, data.class]">
    <div class="group-admin-name__name" :title="props.row[props.column.key]">
      {{ props.row[props.column.key] }}
    </div>
    <a
      class="group-admin-name__menu"
      @click.prevent="
        listeners['edit-group'] &&
          listeners['edit-group']({
            group: props.row,
            target: $event.currentTarget,
          })
      "
    >
      <i class="fas fa-ellipsis-h"></i>
    </a>
  </div>
</template>

<script>
export default {
  name: 'GroupNameField',
  functional: true,
  props: {
    row: {
      required: true,
      type: Object,
    },
    column: {
      required: true,
      type: Object,
    },
  },
}
</script>
