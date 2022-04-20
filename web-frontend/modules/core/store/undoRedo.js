import UndoRedoService from '@baserow/modules/core/services/undoRedo'
import {
  UNDO_REDO_RESULT_CODES,
  UNDO_REDO_STATES,
} from '@baserow/modules/core/utils/undoRedoConstants'
import Vue from 'vue'

export const state = () => ({
  undoing: false,
  redoing: false,
  // A stack of objects, each object representing a set of visible action scopes.
  // The last object in the stack is the current set of scopes which are visible.
  actionScopesStack: [{}],
})

export const mutations = {
  SET_UNDOING(state, value) {
    state.undoing = value
  },
  SET_REDOING(state, value) {
    state.redoing = value
  },
  RESET_ACTION_SCOPE_SET_STACK(state, newScopeSet) {
    state.actionScopesStack = [newScopeSet]
  },
  PUSH_NEW_ACTION_SCOPE_SET(state, newScopeSet) {
    state.actionScopesStack.push(newScopeSet)
  },
  POP_CURRENT_ACTION_SCOPE_SET(state) {
    state.actionScopesStack.pop()
  },
  UPDATE_CURRENT_SCOPE_SET(state, newScope) {
    const current = state.actionScopesStack[state.actionScopesStack.length - 1]
    Object.assign(current, current, newScope)
    for (const [key, value] of Object.entries(newScope)) {
      const exists = Object.prototype.hasOwnProperty.call(state, key)
      if (exists) {
        current[key] = value
      } else {
        Vue.set(current, key, value)
      }
    }
  },
}

let hideTimeout = null

export const actions = {
  async undo({ dispatch }, { showLoadingNotification }) {
    return await dispatch('action', {
      showLoadingNotification,
      serviceMethod: 'undo',
      doingNotificationState: UNDO_REDO_STATES.UNDOING,
      doneNotificationState: UNDO_REDO_STATES.UNDONE,
      nothingToDoNotificationState: UNDO_REDO_STATES.NO_MORE_UNDO,
      skippedDueToErrorNotificationState: UNDO_REDO_STATES.ERROR_WITH_UNDO,
      commitName: 'SET_UNDOING',
    })
  },
  async redo({ dispatch }, { showLoadingNotification }) {
    return await dispatch('action', {
      showLoadingNotification,
      serviceMethod: 'redo',
      doingNotificationState: UNDO_REDO_STATES.REDOING,
      doneNotificationState: UNDO_REDO_STATES.REDONE,
      nothingToDoNotificationState: UNDO_REDO_STATES.NO_MORE_REDO,
      skippedDueToErrorNotificationState: UNDO_REDO_STATES.ERROR_WITH_REDO,
      commitName: 'SET_REDOING',
    })
  },
  async action(
    { getters, commit, dispatch },
    {
      showLoadingNotification,
      serviceMethod,
      doingNotificationState,
      doneNotificationState,
      nothingToDoNotificationState,
      skippedDueToErrorNotificationState,
      commitName,
    }
  ) {
    if (getters.isUndoing || getters.isRedoing) {
      return
    }

    clearTimeout(hideTimeout)
    commit(commitName, true)
    await dispatch(
      'notification/setUndoRedoState',
      showLoadingNotification
        ? doingNotificationState
        : UNDO_REDO_STATES.HIDDEN,
      { root: true }
    )

    try {
      const { data } = await UndoRedoService(this.$client)[serviceMethod](
        getters.getCurrentScope
      )
      const resultCodeToNotificationState = {
        [UNDO_REDO_RESULT_CODES.SUCCESS]: doneNotificationState,
        [UNDO_REDO_RESULT_CODES.NOTHING_TO_DO]: nothingToDoNotificationState,
        [UNDO_REDO_RESULT_CODES.SKIPPED_DUE_TO_ERROR]:
          skippedDueToErrorNotificationState,
      }
      await dispatch(
        'notification/setUndoRedoState',
        resultCodeToNotificationState[data.result_code],
        {
          root: true,
        }
      )
    } finally {
      hideTimeout = setTimeout(
        () =>
          dispatch('notification/setUndoRedoState', UNDO_REDO_STATES.HIDDEN, {
            root: true,
          }),
        2000
      )
      commit(commitName, false)
    }
  },
  resetScopeSetStack({ commit }, scopeSet) {
    // TODO do we need this? Perhaps when switching route entirely?
    commit('RESET_ACTION_SCOPE_SET_STACK', scopeSet)
  },
  pushNewScopeSet({ commit }, scopeSet) {
    // For use in modals. A modal will push a new scope set when opened restricting
    // the actions available for undo/redo to just those visible from the modal.
    // When the modal closes it should then call popCurrentScopeSet to reset to
    // previous scope set.
    commit('PUSH_NEW_ACTION_SCOPE_SET', scopeSet)
  },
  popCurrentScopeSet({ commit }) {
    commit('POP_CURRENT_ACTION_SCOPE_SET')
  },
  updateCurrentScopeSet({ commit }, scope) {
    commit('UPDATE_CURRENT_SCOPE_SET', scope)
  },
}

export const getters = {
  isUndoing(state) {
    return state.undoing
  },
  isRedoing(state) {
    return state.redoing
  },
  getCurrentScope(state) {
    return state.actionScopesStack[state.actionScopesStack.length - 1]
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
