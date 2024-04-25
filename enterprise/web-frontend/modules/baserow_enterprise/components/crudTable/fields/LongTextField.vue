<template functional>
  <div
    :class="[data.staticClass, data.class, 'long-text-field']"
    :title="props.row[props.column.key]"
    v-on="listeners"
  >
    {{ props.row[props.column.key] }}
  </div>
</template>

<script>
export default {
  name: 'LongTextField',
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
