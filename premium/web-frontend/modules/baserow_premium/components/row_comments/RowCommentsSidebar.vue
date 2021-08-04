<template>
  <div>
    <div v-if="!loaded && loading" class="loading-absolute-center" />
    <div v-else>
      <div class="row-comments">
        <div v-if="totalCount === 0" class="row-comments__empty">
          <i class="row-comments__empty-icon fas fa-comments"></i>
          <div class="row-comments__empty-text">
            No comments for this row yet. Use the form below to add a comment.
          </div>
        </div>
        <div v-else class="row-comments__body">
          <InfiniteScroll
            ref="infiniteScroll"
            :current-count="currentCount"
            :max-count="totalCount"
            :loading="loading"
            :reverse="true"
            @load-next-page="nextPage"
          >
            <template #default>
              <RowComment
                v-for="c in comments"
                :key="'row-comment-' + c.id"
                :comment="c"
              />
            </template>
            <template #end>
              <div class="row-comments__end-line"></div>
            </template>
          </InfiniteScroll>
        </div>
        <div class="row-comments__foot">
          <AutoExpandableTextarea
            ref="AutoExpandableTextarea"
            v-model="comment"
            placeholder="Comment"
            :loading="postingComment"
            @entered="postComment"
          >
          </AutoExpandableTextarea>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { notifyIf } from '@baserow/modules/core/utils/error'
import RowComment from '@baserow_premium/components/row_comments/RowComment'
import InfiniteScroll from '@baserow/modules/core/components/helpers/InfiniteScroll'
import AutoExpandableTextarea from '@baserow_premium/components/helpers/AutoExpandableTextarea'

export default {
  name: 'RowCommentsSidebar',
  components: { AutoExpandableTextarea, InfiniteScroll, RowComment },
  props: {
    table: {
      required: true,
      type: Object,
    },
    row: {
      required: true,
      type: Object,
    },
  },
  data() {
    return {
      comment: '',
    }
  },
  computed: {
    ...mapGetters({
      comments: 'row_comments/getSortedRowComments',
      loading: 'row_comments/getLoading',
      postingComment: 'row_comments/getPostingComment',
      loaded: 'row_comments/getLoaded',
      currentCount: 'row_comments/getCurrentCount',
      totalCount: 'row_comments/getTotalCount',
    }),
  },
  async created() {
    try {
      const tableId = this.table.id
      const rowId = this.row.id
      await this.$store.dispatch('row_comments/fetchRowComments', {
        tableId,
        rowId,
      })
    } catch (e) {
      notifyIf(e, 'application')
    }
  },
  methods: {
    async postComment() {
      if (!this.comment.trim() || this.postingComment) {
        return
      }
      try {
        const tableId = this.table.id
        const rowId = this.row.id
        const comment = this.comment.trim()
        await this.$store.dispatch('row_comments/postComment', {
          tableId,
          rowId,
          comment,
        })
        this.comment = ''
        this.$refs.infiniteScroll.scrollToStart()
      } catch (e) {
        notifyIf(e, 'application')
      }
    },
    async nextPage() {
      try {
        const tableId = this.table.id
        const rowId = this.row.id
        await this.$store.dispatch('row_comments/fetchNextSetOfComments', {
          tableId,
          rowId,
        })
      } catch (e) {
        notifyIf(e, 'application')
      }
    },
  },
}
</script>
