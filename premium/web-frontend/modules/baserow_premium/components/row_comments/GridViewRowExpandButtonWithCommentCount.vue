<template functional>
  <GridViewRowExpandButton
    v-if="
      !props.row ||
      !props.row._.metadata.row_comment_count ||
      !injections.$hasPermission(
        'database.table.list_comments',
        props.table,
        props.workspaceId
      )
    "
    :row="props.row"
    v-on="listeners"
  >
  </GridViewRowExpandButton>
  <a
    v-else
    class="row-comments-expand-button"
    :title="props.row._.metadata.row_comment_count + ' comments'"
    @click="listeners['edit-modal'] && listeners['edit-modal']()"
  >
    <template v-if="props.row._.metadata.row_comment_count < 100">
      {{ props.row._.metadata.row_comment_count }}
    </template>
    <i v-else class="row-comments-expand-button__icon iconoir-multi-bubble"></i>
  </a>
</template>
<script>
import GridViewRowExpandButton from '@baserow/modules/database/components/view/grid/GridViewRowExpandButton'

export default {
  name: 'GridViewRowExpandButtonWithCommentCount',
  functional: true,
  components: { GridViewRowExpandButton },
  inject: { $hasPermission: '$hasPermission' },
}
</script>
