<template>
  <div>
    <template v-if="!hasPremiumFeaturesEnabled">
      <div class="row-comments">
        <div class="row-comments__empty">
          <i class="row-comments__empty-icon fas fa-comments"></i>
          <div class="row-comments__empty-text">
            {{ $t('rowCommentSidebar.onlyPremium') }}
          </div>
          <a class="button button--primary" @click="$refs.premiumModal.show()">
            {{ $t('rowCommentSidebar.more') }}
            <i class="fas fa-unlock"></i>
          </a>
        </div>
        <PremiumModal
          ref="premiumModal"
          :name="$t('rowCommentSidebar.name')"
          :workspace="database.workspace"
        ></PremiumModal>
      </div>
    </template>
    <template v-else>
      <div v-if="!loaded && loading" class="loading-absolute-center" />
      <div v-else>
        <div class="row-comments">
          <div v-if="totalCount === 0" class="row-comments__empty">
            <i class="row-comments__empty-icon fas fa-comments"></i>
            <div class="row-comments__empty-text">
              <template
                v-if="
                  !$hasPermission(
                    'database.table.create_comment',
                    table,
                    database.workspace.id
                  )
                "
                >{{ $t('rowCommentSidebar.readOnlyNoComment') }}</template
              >
              <template v-else>
                {{ $t('rowCommentSidebar.noComment') }}
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
              :render-end="false"
              @load-next-page="nextPage"
            >
              <template #default>
                <div
                  v-for="(c, index) in comments"
                  :key="'row-comment-' + c.id"
                >
                  <div
                    v-if="isNewDayForComments(index)"
                    class="row-comment__day-separator"
                  >
                    <span>{{ formatSeparatorDate(c) }}</span>
                  </div>
                  <RowComment
                    :comment="c"
                    :can-edit="canEditComments"
                    :can-delete="canDeleteComments"
                  />
                </div>
              </template>
            </InfiniteScroll>
          </div>
          <div
            v-if="
              $hasPermission(
                'database.table.create_comment',
                table,
                database.workspace.id
              )
            "
            class="row-comments__foot"
          >
            <RichTextEditor
              v-model="comment"
              :placeholder="$t('rowCommentSidebar.comment')"
              @entered="postComment()"
            />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import moment from '@baserow/modules/core/moment'
import { notifyIf } from '@baserow/modules/core/utils/error'
import RowComment from '@baserow_premium/components/row_comments/RowComment'
import InfiniteScroll from '@baserow/modules/core/components/helpers/InfiniteScroll'
import RichTextEditor from '@baserow/modules/core/components/editor/RichTextEditor.vue'
import PremiumModal from '@baserow_premium/components/PremiumModal'
import PremiumFeatures from '@baserow_premium/features'

export default {
  name: 'RowCommentsSidebar',
  components: {
    InfiniteScroll,
    RowComment,
    PremiumModal,
    RichTextEditor,
  },
  props: {
    database: {
      type: Object,
      required: true,
    },
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
    hasPremiumFeaturesEnabled() {
      return this.$hasFeature(
        PremiumFeatures.PREMIUM,
        this.database.workspace.id
      )
    },
    ...mapGetters({
      loggedUserId: 'auth/getUserId',
      comments: 'row_comments/getSortedRowComments',
      loading: 'row_comments/getLoading',
      loaded: 'row_comments/getLoaded',
      currentCount: 'row_comments/getCurrentCount',
      totalCount: 'row_comments/getTotalCount',
      additionalUserData: 'auth/getAdditionalUserData',
    }),
    canEditComments() {
      return this.$hasPermission(
        'database.table.update_comment',
        this.table,
        this.database.workspace.id
      )
    },
    canDeleteComments() {
      return this.$hasPermission(
        'database.table.delete_comment',
        this.table,
        this.database.workspace.id
      )
    },
    isNewDayForComments() {
      return (index) => {
        if (index === this.comments.length - 1) {
          return true
        }
        const tzone = moment.tz.guess()
        const previousCreationDate = moment
          .utc(this.comments[index].created_on)
          .tz(tzone)
        const currentCreationDate = moment
          .utc(this.comments[index + 1].created_on)
          .tz(tzone)
        return !previousCreationDate.isSame(currentCreationDate, 'day')
      }
    },
  },
  watch: {
    async hasPremiumFeaturesEnabled() {
      await this.initialLoad()
    },
  },
  async created() {
    await this.initialLoad()
  },
  methods: {
    async initialLoad() {
      if (!this.hasPremiumFeaturesEnabled) {
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
    formatSeparatorDate(comment) {
      return moment
        .utc(comment.created_on)
        .tz(moment.tz.guess())
        .calendar(null, {
          sameDay: '[Today]',
          lastDay: '[Yesterday]',
          lastWeek: 'LL',
          sameElse: 'LL',
        })
    },
    async postComment() {
      const comment = this.comment
      if (
        !comment ||
        !this.$hasPermission(
          'database.table.create_comment',
          this.table,
          this.database.workspace.id
        )
      ) {
        return
      }
      try {
        this.comment = ''
        await this.$store.dispatch('row_comments/postComment', {
          tableId: this.table.id,
          rowId: this.row.id,
          message: comment,
        })
        this.$refs.infiniteScroll.scrollToStart()
      } catch (e) {
        notifyIf(e, 'application')
      }
    },
    async nextPage() {
      try {
        await this.$store.dispatch('row_comments/fetchNextSetOfComments', {
          tableId: this.table.id,
          rowId: this.row.id,
        })
      } catch (e) {
        notifyIf(e, 'application')
      }
    },
  },
}
</script>
