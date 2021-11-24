<template>
  <div>
    <template v-if="!validPremiumLicense">
      <div class="row-comments">
        <div class="row-comments__empty">
          <i class="row-comments__empty-icon fas fa-comments"></i>
          <div class="row-comments__empty-text">
            Row comments are available in the premium version.
          </div>
        </div>
      </div>
    </template>
    <template v-else>
      <div v-if="!loaded && loading" class="loading-absolute-center" />
      <div v-else>
        <div class="row-comments">
          <div v-if="totalCount === 0" class="row-comments__empty">
            <i class="row-comments__empty-icon fas fa-comments"></i>
            <div class="row-comments__empty-text">
              <template v-if="readOnly">No comments for this row.</template>
              <template v-else>
                No comments for this row yet. Use the form below to add a
                comment.
              </template>
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
          <div v-if="!readOnly" class="row-comments__foot">
            <AutoExpandableTextareaInput
              ref="AutoExpandableTextarea"
              v-model="comment"
              placeholder="Comment"
              @entered="postComment"
            >
            </AutoExpandableTextareaInput>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { PremiumPlugin } from '@baserow_premium/plugins'
import RowComment from '@baserow_premium/components/row_comments/RowComment'
import InfiniteScroll from '@baserow/modules/core/components/helpers/InfiniteScroll'
import AutoExpandableTextareaInput from '@baserow/modules/core/components/helpers/AutoExpandableTextareaInput'

export default {
  name: 'RowCommentsSidebar',
  components: {
    AutoExpandableTextareaInput,
    InfiniteScroll,
    RowComment,
  },
  props: {
    table: {
      required: true,
      type: Object,
    },
    row: {
      required: true,
      type: Object,
    },
    readOnly: {
      required: true,
      type: Boolean,
    },
  },
  data() {
    return {
      comment: '',
    }
  },
  computed: {
    validPremiumLicense() {
      return PremiumPlugin.hasValidPremiumLicense(this.additionalUserData)
    },
    ...mapGetters({
      comments: 'row_comments/getSortedRowComments',
      loading: 'row_comments/getLoading',
      loaded: 'row_comments/getLoaded',
      currentCount: 'row_comments/getCurrentCount',
      totalCount: 'row_comments/getTotalCount',
      additionalUserData: 'auth/getAdditionalUserData',
    }),
  },
  async created() {
    if (!this.validPremiumLicense) {
      return
    }

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
      const comment = this.comment.trim()
      if (!comment || this.readOnly) {
        return
      }
      try {
        const tableId = this.table.id
        const rowId = this.row.id
        this.comment = ''
        await this.$store.dispatch('row_comments/postComment', {
          tableId,
          rowId,
          comment,
        })
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
