import axios from 'axios'

import { upperCaseFirst } from '@baserow/modules/core/utils/string'

export class ResponseErrorMessage {
  constructor(title, message) {
    this.title = title
    this.message = message
  }
}

/**
 * This class holds all the default error messages and offers the ability to
 * register new ones. This is stored in a separate class because need to inject
 * this, so it can be used by other modules.
 */
class ClientErrorMap {
  constructor() {
    // Declare the default error messages.
    this.errorMap = {
      ERROR_USER_NOT_IN_GROUP: new ResponseErrorMessage(
        'Action not allowed.',
        "The action couldn't be completed because you aren't a " +
          'member of the related group.'
      ),
      ERROR_USER_INVALID_GROUP_PERMISSIONS: new ResponseErrorMessage(
        'Action not allowed.',
        "The action couldn't be completed because you don't have the right " +
          'permissions to the related group.'
      ),
      // @TODO move these errors to the module.
      ERROR_TABLE_DOES_NOT_EXIST: new ResponseErrorMessage(
        "Table doesn't exist.",
        "The action couldn't be completed because the related table doesn't exist" +
          ' anymore.'
      ),
      ERROR_ROW_DOES_NOT_EXIST: new ResponseErrorMessage(
        "Row doesn't exist.",
        "The action couldn't be completed because the related row doesn't exist" +
          ' anymore.'
      ),
      ERROR_FILE_SIZE_TOO_LARGE: new ResponseErrorMessage(
        'File to large',
        'The provided file is too large.'
      ),
      ERROR_INVALID_FILE: new ResponseErrorMessage(
        'Invalid file',
        'The provided file is not a valid file.'
      ),
      ERROR_FILE_URL_COULD_NOT_BE_REACHED: new ResponseErrorMessage(
        'Invalid URL',
        'The provided file URL could not be reached.'
      ),
      ERROR_INVALID_FILE_URL: new ResponseErrorMessage(
        'Invalid URL',
        'The provided file URL is invalid or not allowed.'
      ),
      USER_ADMIN_CANNOT_DEACTIVATE_SELF: new ResponseErrorMessage(
        'Action not allowed.',
        'You cannot de-activate or un-staff yourself.'
      ),
      USER_ADMIN_CANNOT_DELETE_SELF: new ResponseErrorMessage(
        'Action not allowed.',
        'You cannot delete yourself.'
      ),
      ERROR_MAX_FIELD_COUNT_EXCEEDED: new ResponseErrorMessage(
        "Couldn't create field.",
        "The action couldn't be completed because the field count exceeds the limit"
      ),
      ERROR_CANNOT_RESTORE_PARENT_BEFORE_CHILD: new ResponseErrorMessage(
        'Please restore the parent first.',
        'You cannot restore this item because it depends on a deleted item.' +
          ' Please restore the parent item first.'
      ),
      ERROR_GROUP_USER_IS_LAST_ADMIN: new ResponseErrorMessage(
        "Can't leave the group",
        "It's not possible to leave the group because you're the last admin. Please" +
          ' delete the group or give another user admin permissions.'
      ),
    }
  }

  setError(code, title, description) {
    this.errorMap[code] = new ResponseErrorMessage(title, description)
  }
}

export class ErrorHandler {
  constructor(store, clientErrorMap, response, code = null, detail = null) {
    this.isHandled = false
    this.store = store
    this.response = response
    this.setError(code, detail)
    this.errorMap = clientErrorMap.errorMap

    // A temporary notFoundMap containing the error messages for when the
    // response contains a 404 error based on the provided context name. Note
    // that an entry is not found a default message will be generated.
    this.notFoundMap = {}
  }

  /**
   * Changes the error code and details.
   */
  setError(code, detail) {
    this.code = code
    this.detail = detail
  }

  /**
   * Returns true if there is a readable error.
   * @return {boolean}
   */
  hasError() {
    return this.response !== undefined && this.response.code !== null
  }

  /**
   * Returns true is the response status code is equal to not found (404).
   * @return {boolean}
   */
  isNotFound() {
    return this.response !== undefined && this.response.status === 404
  }

  /**
   * Returns true if the response status code is equal to not found (429) which
   * means that the user is sending too much requests to the server.
   * @return {boolean}
   */
  isTooManyRequests() {
    return this.response !== undefined && this.response.status === 429
  }

  /**
   * Return true if there is a network error.
   * @return {boolean}
   */
  hasNetworkError() {
    return this.response === undefined
  }

  /**
   * Finds a message in the global errors or in the provided specific error map.
   */
  getErrorMessage(specificErrorMap = null) {
    if (
      specificErrorMap !== null &&
      Object.prototype.hasOwnProperty.call(specificErrorMap, this.code)
    ) {
      return specificErrorMap[this.code]
    }

    if (Object.prototype.hasOwnProperty.call(this.errorMap, this.code)) {
      return this.errorMap[this.code]
    }

    return new ResponseErrorMessage(
      'Action not completed.',
      "The action couldn't be completed because an unknown error has" +
        ' occured.'
    )
  }

  /**
   * Finds a not found message for a given context.
   */
  getNotFoundMessage(name) {
    if (!Object.prototype.hasOwnProperty.call(this.notFoundMap, name)) {
      return new ResponseErrorMessage(
        `${upperCaseFirst(name)} not found.`,
        `The selected ${name.toLowerCase()} wasn't found, maybe it has already been deleted.`
      )
    }
    return this.notFoundMap[name]
  }

  /**
   * Returns a standard network error message. For example if the API server
   * could not be reached.
   */
  getNetworkErrorMessage() {
    return new ResponseErrorMessage(
      'Network error',
      'Could not connect to the API server.'
    )
  }

  /**
   * Returns a standard network error message. For example if the API server
   * could not be reached.
   */
  getTooManyRequestsError() {
    return new ResponseErrorMessage(
      'Too many requests',
      'You are sending too many requests to the server. Please wait a moment.'
    )
  }

  /**
   * If there is an error or the requested detail is not found an error
   * message related to the problem is returned.
   */
  getMessage(name = null, specificErrorMap = null) {
    if (this.isTooManyRequests()) {
      return this.getTooManyRequestsError()
    }
    if (this.hasNetworkError()) {
      return this.getNetworkErrorMessage()
    }
    if (this.hasError()) {
      return this.getErrorMessage(specificErrorMap)
    }
    if (this.isNotFound()) {
      return this.getNotFoundMessage(name)
    }
    return null
  }

  /**
   * If there is an error or the requested detail is not found we will try to
   * get find an existing message of one is not provided and notify the user
   * about what went wrong. After that the error is marked as handled.
   */
  notifyIf(name = null, message = null) {
    if (
      !(this.hasError() || this.hasNetworkError() || this.isNotFound()) ||
      this.isHandled
    ) {
      return
    }

    if (message === null) {
      message = this.getMessage(name)
    }

    this.store.dispatch(
      'notification/error',
      {
        title: message.title,
        message: message.message,
      },
      { root: true }
    )

    this.handled()
  }

  /**
   * Will mark the error as handled so that the same error message isn't shown
   * twice.
   */
  handled() {
    this.isHandled = true
  }
}

export default function ({ store, app }, inject) {
  // Create and inject the client error map, so that other modules can also register
  // default error messages.
  const clientErrorMap = new ClientErrorMap(app)
  inject('clientErrorMap', clientErrorMap)

  const url =
    (process.client
      ? app.$env.PUBLIC_BACKEND_URL
      : app.$env.PRIVATE_BACKEND_URL) + '/api'
  const client = axios.create({
    baseURL: url,
    withCredentials: false,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
  })

  // Create a request interceptor to add the authorization token to every
  // request if the user is authenticated.
  client.interceptors.request.use((config) => {
    if (store.getters['auth/isAuthenticated']) {
      const token = store.getters['auth/token']
      config.headers.Authorization = `JWT ${token}`
    }
    if (store.getters['auth/webSocketId'] !== null) {
      const webSocketId = store.getters['auth/webSocketId']
      config.headers.WebSocketId = webSocketId
    }
    return config
  })

  // Create a response interceptor to add more detail tot the error message
  // and to create a notification when there is a network error.
  client.interceptors.response.use(
    (response) => {
      return response
    },
    (error) => {
      error.handler = new ErrorHandler(store, clientErrorMap, error.response)

      // Add the error message in the response to the error object.
      if (
        error.response &&
        typeof error.response.data === 'object' &&
        'error' in error.response.data &&
        'detail' in error.response.data
      ) {
        error.handler.setError(
          error.response.data.error,
          error.response.data.detail
        )
      }

      return Promise.reject(error)
    }
  )

  inject('client', client)
}
