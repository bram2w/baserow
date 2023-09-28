<template functional>
  <div class="data-table__more-wrapper">
    <a
      class="data-table__more"
      @click.prevent="
        listeners['row-context'] &&
          listeners['row-context']({
            row: props.row,
            event: $event,
            target: $event.currentTarget,
            time: Date.now(),
          })
      "
    >
      <i class="data-table__more-icon baserow-icon-more-horizontal"></i>
    </a>
  </div>
</template>

<script>
export default {
  name: 'MoreField',
  functional: true,
  props: {
    row: {
      required: true,
      type: Object,
    },
  },
}
</script>
