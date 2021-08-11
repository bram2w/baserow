import _ from 'lodash'

import moment from '@baserow/modules/core/moment'

import RowCommentService from '@baserow_premium/services/row_comments/row_comments'

export const state = () => ({
  comments: [],
  loading: false,
  loaded: false,
  currentCount: 0,
  totalCount: 0,
  loadedRowId: false,
  loadedTableId: false,
  nextTemporaryCommentId: -1,
})

function populateComment(comment, loading) {
  comment._ = {
    loading,
  }
  return comment
}

export const mutations = {
  /**
   * Adds a list of comments to the existing comments, ensuring that the end result of
   * comments is an ordered list of comments descending by ID with no duplicate
   * comments. If a comment with the same id as an existing comment is provided in the
   * list the existing comment will be replaced by the new one.
   *
   * We want to handle duplicates here as comments received as realtime events could
   * potentially be also loaded in via a normal backend api fetch call.
   */
  ADD_ROW_COMMENTS(state, { comments, loading }) {
    comments.forEach((newComment) => {
      newComment = populateComment(newComment, loading)
      const existingIndex = state.comments.findIndex(
        (c) => c.id === newComment.id
      )
      if (existingIndex >= 0) {
        // Prevent duplicates by just replacing them inline
        state.comments.splice(existingIndex, 0, newComment)
      } else {
        state.comments.push(newComment)
      }
    })
    state.currentCount = state.comments.length
  },
  REMOVE_ROW_COMMENT(state, id) {
    const existingIndex = state.comments.findIndex((c) => c.id === id)
    if (existingIndex >= 0) {
      state.comments.splice(existingIndex, 1)
    }
  },
  RESET_ROW_COMMENTS(state) {
    state.comments = []
  },
  SET_LOADING(state, loading) {
    state.loading = loading
  },
  SET_LOADED(state, loaded) {
    state.loaded = loaded
  },
  SET_NEXT_TEMPORARY_COMMENT_ID(state, nextTemporaryCommentId) {
    state.nextTemporaryCommentId = nextTemporaryCommentId
  },
  SET_LOADED_TABLE_AND_ROW(state, { tableId, rowId }) {
    state.loadedRowId = rowId
    state.loadedTableId = tableId
  },
  SET_TOTAL_COUNT(state, totalCount) {
    state.totalCount = totalCount
  },
}

export const actions = {
  /**
   * Fetches the initial row comments to display for a given table and row. Resets any
   * existing comments entirely.
   */
  async fetchRowComments(
    { dispatch, commit, getters, state },
    { tableId, rowId }
  ) {
    commit('SET_LOADING', true)
    commit('SET_LOADED', false)
    try {
      const { data } = await RowCommentService(this.$client).fetchAll(
        tableId,
        rowId,
        {}
      )
      commit('RESET_ROW_COMMENTS')
      commit('ADD_ROW_COMMENTS', { comments: data.results, loading: false })
      commit('SET_TOTAL_COUNT', data.count)
      commit('SET_LOADED_TABLE_AND_ROW', { tableId, rowId })
      commit('SET_LOADED', true)
    } finally {
      commit('SET_LOADING', false)
    }
  },
  /**
   * Fetches the next 10 comments from the server and adds them to the comments list.
   */
  async fetchNextSetOfComments(
    { dispatch, commit, getters, state },
    { tableId, rowId }
  ) {
    commit('SET_LOADING', true)
    try {
      // We have to use offset based paging here as new comments can be added by the
      // user or come in via realtime events.
      const { data } = await RowCommentService(this.$client).fetchAll(
        tableId,
        rowId,
        { offset: state.currentCount }
      )
      commit('ADD_ROW_COMMENTS', { comments: data.results, loading: false })
      commit('SET_TOTAL_COUNT', data.count)
    } finally {
      commit('SET_LOADING', false)
    }
  },
  /**
   * Posts a new comment to the server and updates the comments list once the server
   * responds with it's id and other related comment data.
   */
  async postComment(
    { commit, state, rootGetters, dispatch },
    { tableId, rowId, comment }
  ) {
    const temporaryId = state.nextTemporaryCommentId
    commit('SET_NEXT_TEMPORARY_COMMENT_ID', temporaryId - 1)
    try {
      // Immediately add the row comment to the UI to be replaced by the real comment
      // later from the server.
      const temporaryComment = {
        created_on: moment().toISOString(),
        updated_on: moment().toISOString(),
        comment,
        row_id: rowId,
        table_id: tableId,
        user_id: rootGetters['auth/getUserId'],
        first_name: rootGetters['auth/getName'],
        id: temporaryId,
      }
      commit('ADD_ROW_COMMENTS', {
        comments: [temporaryComment],
        loading: true,
      })
      const { data } = await RowCommentService(this.$client).create(
        tableId,
        rowId,
        comment
      )
      commit('REMOVE_ROW_COMMENT', temporaryId)
      dispatch('forceCreate', { rowComment: data })
    } catch (e) {
      // Make sure we remove the temporary comment if the create call failed.
      commit('REMOVE_ROW_COMMENT', temporaryId)
      throw e
    }
  },
  async forceCreate(context, { rowComment }) {
    const { commit, state } = context
    if (
      state.loadedTableId === rowComment.table_id &&
      state.loadedRowId === rowComment.row_id
    ) {
      commit('ADD_ROW_COMMENTS', { comments: [rowComment], loading: false })
      commit('SET_TOTAL_COUNT', state.totalCount + 1)
    }
    // A new comment has been forcibly created so we need to let all views know that
    // the row comment count metadata should be incremented atomically.
    for (const viewType of Object.values(this.$registry.getAll('view'))) {
      await viewType.rowMetadataUpdated(
        { store: this },
        rowComment.table_id,
        rowComment.row_id,
        'row_comment_count',
        (count) => (count ? count + 1 : 1),
        'page/'
      )
    }
  },
}

export const getters = {
  getSortedRowComments(state) {
    return _.sortBy(state.comments, (c) => -moment.utc(c.created_on))
  },
  getCurrentCount(state) {
    return state.currentCount
  },
  getTotalCount(state) {
    return state.totalCount
  },
  getLoading(state) {
    return state.loading
  },
  getLoaded(state) {
    return state.loaded
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
