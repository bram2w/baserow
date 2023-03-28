export const UNDO_REDO_STATES = {
  // The undo has successfully completed
  UNDONE: 'UNDONE',
  // The redo has successfully completed
  REDONE: 'REDONE',
  // The undo action is currently executing
  UNDOING: 'UNDOING',
  // The redo action is currently executing
  REDOING: 'REDOING',
  // An undo was requested but there were no more actions to undo
  NO_MORE_UNDO: 'NO_MORE_UNDO',
  // An redo was requested but there were no more actions to undo
  NO_MORE_REDO: 'NO_MORE_REDO',
  // Something went wrong whilst undoing and so the undo was skipped over
  ERROR_WITH_UNDO: 'ERROR_WITH_UNDO',
  // Something went wrong whilst redoing and so the redo was skipped over
  ERROR_WITH_REDO: 'ERROR_WITH_REDO',
  // There is no recent undo/redo action
  HIDDEN: 'HIDDEN',
}
// The core types of undo/redo scopes available.
export const CORE_ACTION_SCOPES = {
  root(enabled = true) {
    return {
      root: enabled,
    }
  },
  workspace(workspaceId) {
    return {
      workspace: workspaceId,
    }
  },
  application(applicationId) {
    return {
      application: applicationId,
    }
  },
}

// Please keep in sync with baserow.api.user.serializers.UndoRedoResponseSerializer
export const UNDO_REDO_RESULT_CODES = {
  NOTHING_TO_DO: 'NOTHING_TO_DO',
  SUCCESS: 'SUCCESS',
  SKIPPED_DUE_TO_ERROR: 'SKIPPED_DUE_TO_ERROR',
}
