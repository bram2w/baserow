<template functional>
  <div :class="[data.staticClass, data.class]" v-on="listeners">
    <div v-if="props.row[props.column.key]">
      <i
        class="fas fa-fw fa-check user-admin-active__icon user-admin-active__icon--activated"
      ></i>
      Active
    </div>
    <div v-else>
      <i
        class="fas fa-fw fa-times user-admin-active__icon user-admin-active__icon--deactivated"
      ></i>
      Deactivated
    </div>
  </div>
</template>

<script>
export default {
  name: 'ActiveField',
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
