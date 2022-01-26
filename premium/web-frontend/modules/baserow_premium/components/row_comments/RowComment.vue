<template>
  <div
    :class="{ 'row-comments__comment--right': ownComment }"
    class="row-comments__comment"
  >
    <div class="row-comments__comment-head">
      <div class="row-comments__comment-head-initial">
        {{ comment.first_name | nameAbbreviation }}
      </div>
      <div class="row-comments__comment-head-details">
        <div class="row-comments__comment-head-name">
          {{ ownComment ? $t('rowComment.you') : comment.first_name }}
        </div>
        <div :title="localTimestamp" class="row-comments__comment-head-time">
          {{ timeAgo }}
        </div>
      </div>
    </div>
    <div class="row-comments__comment-text">{{ comment.comment }}</div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import moment from '@baserow/modules/core/moment'

export default {
  name: 'RowComment',
  props: {
    comment: {
      type: Object,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      userId: 'auth/getUserId',
    }),
    ownComment() {
      return this.comment.user_id === this.userId
    },
    timeAgo() {
      return moment.utc(this.comment.created_on).fromNow()
    },
    localTimestamp() {
      return moment.utc(this.comment.created_on).format('L LT')
    },
  },
}
</script>
