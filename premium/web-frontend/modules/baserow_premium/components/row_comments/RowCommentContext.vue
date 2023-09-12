<template>
  <Context
    ref="context"
    :overflow-scroll="true"
    :max-height-if-outside-viewport="true"
  >
    <div>
      <ul class="context__menu">
        <li class="edit">
          <a :class="{ disabled: !canEdit }" @click.prevent="editComment">
            <i class="context__menu-icon fas fa-pen"></i>
            <span> {{ $t('rowCommentContext.edit') }} </span>
          </a>
        </li>
        <li class="delete">
          <a :class="{ disabled: !canDelete }" @click.prevent="deleteComment">
            <i class="context__menu-icon fas fa-trash"></i>
            <span> {{ $t('rowCommentContext.delete') }} </span>
          </a>
        </li>
      </ul>
    </div>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'RowCommentContext',
  mixins: [context],
  props: {
    canEdit: {
      type: Boolean,
      required: true,
    },
    canDelete: {
      type: Boolean,
      required: true,
    },
  },
  methods: {
    editComment() {
      if (this.canEdit) {
        this.$emit('edit')
      }
    },
    deleteComment() {
      if (this.canDelete) {
        this.$emit('delete')
      }
    },
  },
}
</script>
