<template>
  <div
    :class="{
      'row-comments__comment--right': ownComment,
      'row-comments__comment--editing': editing,
    }"
    class="row-comments__comment"
  >
    <div class="row-comments__comment-head">
      <div
        class="row-comments__comment-head-details"
        :class="{ 'row-comments__comment-head-details--right': ownComment }"
      >
        <div v-if="!ownComment" class="row-comments__comment-head-initial">
          {{ firstName | nameAbbreviation }}
        </div>
        <div class="row-comments__comment-head-name">
          {{ ownComment ? $t('rowComment.you') : firstName }}
        </div>
        <div :title="timeTooltip" class="row-comments__comment-head-time">
          <span>{{ localCreationTime }}</span>
          <span v-if="comment.edited && !comment.trashed">
            ({{ $t('rowComment.edited') }})
          </span>
        </div>
        <a
          v-if="ownComment && !editing && (!comment.trashed || deleting)"
          ref="commentContextLink"
          :class="{ disabled: operationPending }"
          class="row-comments__comment-context"
          @click.prevent="openRowCommentContext"
        >
          <i
            class="fas fa-ellipsis-h"
            :class="{ pending: operationPending }"
          ></i>
        </a>
        <RowCommentContext
          ref="commentContext"
          :comment="comment"
          :can-edit="canEdit"
          :can-delete="canDelete && !creating"
          @edit="startEdit"
          @delete="deleteComment"
        ></RowCommentContext>
      </div>
    </div>
    <div v-if="editing">
      <AutoExpandableTextareaInput
        ref="autoExpandableTextareaInput"
        v-model="commentText"
        class="row-comments__comment-text row-comments__comment-text--editing"
        @entered="stopEdit(true)"
      >
      </AutoExpandableTextareaInput>
      <div class="row_comments__comment-text-actions">
        <button
          class="button button--ghost"
          :disabled="updating"
          @click="stopEdit()"
        >
          {{ $t('action.cancel') }}
        </button>
        <button class="button button--primary" @click="stopEdit(true)">
          {{ $t('action.save') }}
        </button>
      </div>
    </div>
    <div
      v-else-if="comment.trashed"
      class="row-comments__comment-text row-comments__comment-text--trashed"
    >
      {{ $t('rowComment.commentTrashed') }}
    </div>
    <div v-else class="row-comments__comment-text">{{ comment.comment }}</div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { notifyIf } from '@baserow/modules/core/utils/error'
import RowCommentContext from '@baserow_premium/components/row_comments/RowCommentContext'
import AutoExpandableTextareaInput from '@baserow/modules/core/components/helpers/AutoExpandableTextareaInput'

import moment from '@baserow/modules/core/moment'

export default {
  name: 'RowComment',
  components: {
    AutoExpandableTextareaInput,
    RowCommentContext,
  },
  props: {
    comment: {
      type: Object,
      required: true,
    },
    canEdit: {
      type: Boolean,
      required: true,
    },
    canDelete: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      editing: false,
      updating: false,
      deleting: false,
      commentText: '',
    }
  },
  computed: {
    ...mapGetters({
      userId: 'auth/getUserId',
    }),
    creating() {
      return this.comment.isTemporary
    },
    operationPending() {
      return this.creating || this.updating || this.deleting
    },

    firstName() {
      if (this.comment.user_id === null) {
        return this.$t('rowComment.anonymous')
      }
      return this.comment.first_name
    },
    ownComment() {
      return this.comment.user_id === this.userId
    },
    localCreationTime() {
      return this.getLocalizedMoment(this.comment.created_on).format('LT')
    },
    localCreationDateTime() {
      return this.getLocalizedMoment(this.comment.created_on).format('L LT')
    },
    localUpdatedDateTime() {
      return this.getLocalizedMoment(this.comment.updated_on).format('L LT')
    },
    timeTooltip() {
      if (this.operationPending) {
        if (this.creating) {
          return this.$t('rowComment.creating')
        } else if (this.updating) {
          return this.$t('rowComment.updating')
        } else if (this.deleting) {
          return this.$t('rowComment.deleting')
        }
      }
      let tooltip =
        this.$t('rowComment.created') + `: ${this.localCreationDateTime}`
      if (this.comment.edited) {
        tooltip += `\n${this.$t('rowComment.edited')}:   ${
          this.localUpdatedDateTime
        }`
      }
      return tooltip
    },
  },
  unmounted() {
    if (this.$el.onClickOutside) {
      document.removeEventListener('click', this.$el.onClickOutside)
    }
  },
  methods: {
    getLocalizedMoment(timestamp) {
      return moment.utc(timestamp).tz(moment.tz.guess())
    },
    openRowCommentContext() {
      if (!this.operationPending) {
        this.$refs.commentContext.toggle(
          this.$refs.commentContextLink,
          'bottom',
          'right',
          0
        )
      }
    },
    startEdit() {
      this.commentText = this.comment.comment
      this.$refs.commentContext.hide()
      this.editing = true

      this.$el.onClickOutside = (evt) => {
        if (
          !this.$el.contains(evt.target) &&
          !this.$refs.commentContext.$el.contains(evt.target)
        ) {
          this.stopEdit()
        }
      }
      document.addEventListener('click', this.$el.onClickOutside)

      this.$nextTick(() => {
        this.$refs.autoExpandableTextareaInput.focus()
      })
    },
    async stopEdit(save = false) {
      document.removeEventListener('click', this.$el.onClickOutside)
      this.editing = false

      if (save) {
        await this.updateComment()
      } else {
        this.commentText = this.comment.comment
      }
    },
    async updateComment() {
      if (!this.commentText) {
        return
      }

      this.updating = true
      try {
        await this.$store.dispatch('row_comments/updateComment', {
          tableId: this.comment.table_id,
          commentId: this.comment.id,
          commentText: this.commentText,
        })
      } catch (error) {
        notifyIf(error, 'application')
      } finally {
        this.updating = false
      }
    },
    async deleteComment() {
      this.deleting = true
      this.$refs.commentContext.hide()

      try {
        await this.$store.dispatch('row_comments/deleteComment', {
          tableId: this.comment.table_id,
          rowId: this.comment.row_id,
          commentId: this.comment.id,
        })
      } catch (error) {
        notifyIf(error, 'application')
      } finally {
        this.deleting = false
      }
    },
  },
}
</script>
