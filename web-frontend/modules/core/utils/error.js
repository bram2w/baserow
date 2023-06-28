/**
 * Adds a toast error if the error response has 404 status code.
 */
export function notifyIf404(dispatch, error, title, message) {
  if (error.response && error.response.status === 404) {
    dispatch(
      'toast/error',
      {
        title,
        message,
      },
      { root: true }
    )
  }
}

/**
 * Small helper function that checks if the error handler is present in the
 * error, if so, the notify if function will be called to communicate the error
 * to the user, but if not the error will be trowed so proper action can be
 * taken.
 */
export function notifyIf(error, name = null) {
  if (error.handler) {
    error.handler.notifyIf(name)
  } else {
    throw error
  }
}
