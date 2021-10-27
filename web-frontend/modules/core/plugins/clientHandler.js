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
  constructor(app) {
    // Declare the default error messages.
    this.errorMap = {
      ERROR_USER_NOT_IN_GROUP: new ResponseErrorMessage(
        app.i18n.t('clientHandler.userNotInGroupTitle'),
        app.i18n.t('clientHandler.userNotInGroupDescription')
      ),
      ERROR_USER_INVALID_GROUP_PERMISSIONS: new ResponseErrorMessage(
        app.i18n.t('clientHandler.invalidGroupPermissionsTitle'),
        app.i18n.t('clientHandler.invalidGroupPermissionsDescription')
      ),
      // @TODO move these errors to the module.
      ERROR_TABLE_DOES_NOT_EXIST: new ResponseErrorMessage(
        app.i18n.t('clientHandler.tableDoesNotExistTitle'),
        app.i18n.t('clientHandler.tableDoesNotExistDescription')
      ),
      ERROR_ROW_DOES_NOT_EXIST: new ResponseErrorMessage(
        app.i18n.t('clientHandler.rowDoesNotExistTitle'),
        app.i18n.t('clientHandler.rowDoesNotExistDescription')
      ),
      ERROR_FILE_SIZE_TOO_LARGE: new ResponseErrorMessage(
        app.i18n.t('clientHandler.fileSizeTooLargeTitle'),
        app.i18n.t('clientHandler.fileSizeTooLargeDescription')
      ),
      ERROR_INVALID_FILE: new ResponseErrorMessage(
        app.i18n.t('clientHandler.invalidFileTitle'),
        app.i18n.t('clientHandler.invalidFileDescription')
      ),
      ERROR_FILE_URL_COULD_NOT_BE_REACHED: new ResponseErrorMessage(
        app.i18n.t('clientHandler.fileUrlCouldNotBeReachedTitle'),
        app.i18n.t('clientHandler.fileUrlCouldNotBeReachedDescription')
      ),
      ERROR_INVALID_FILE_URL: new ResponseErrorMessage(
        app.i18n.t('clientHandler.invalidFileUrlTitle'),
        app.i18n.t('clientHandler.invalidFileUrlDescription')
      ),
      USER_ADMIN_CANNOT_DEACTIVATE_SELF: new ResponseErrorMessage(
        app.i18n.t('clientHandler.adminCannotDeactivateSelfTitle'),
        app.i18n.t('clientHandler.adminCannotDeactivateSelfDescription')
      ),
      USER_ADMIN_CANNOT_DELETE_SELF: new ResponseErrorMessage(
        app.i18n.t('clientHandler.adminCannotDeleteSelfTitle'),
        app.i18n.t('clientHandler.adminCannotDeleteSelfDescription')
      ),
      ERROR_MAX_FIELD_COUNT_EXCEEDED: new ResponseErrorMessage(
        app.i18n.t('clientHandler.maxFieldCountExceededTitle'),
        app.i18n.t('clientHandler.maxFieldCountExceededDescription')
      ),
      ERROR_CANNOT_RESTORE_PARENT_BEFORE_CHILD: new ResponseErrorMessage(
        app.i18n.t('clientHandler.cannotRestoreParentBeforeChildTitle'),
        app.i18n.t('clientHandler.cannotRestoreParentBeforeChildDescription')
      ),
      ERROR_GROUP_USER_IS_LAST_ADMIN: new ResponseErrorMessage(
        app.i18n.t('clientHandler.groupUserIsLastAdminTitle'),
        app.i18n.t('clientHandler.groupUserIsLastAdminDescription')
      ),
    }
  }

  setError(code, title, description) {
    this.errorMap[code] = new ResponseErrorMessage(title, description)
  }
}

export class ErrorHandler {
  constructor(
    store,
    app,
    clientErrorMap,
    response,
    code = null,
    detail = null
  ) {
    this.isHandled = false
    this.store = store
    this.app = app
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
      this.app.i18n.t('clientHandler.notCompletedTitle'),
      this.app.i18n.t('clientHandler.notCompletedDescription')
    )
  }

  /**
   * Finds a not found message for a given context.
   */
  getNotFoundMessage(name) {
    if (!Object.prototype.hasOwnProperty.call(this.notFoundMap, name)) {
      return new ResponseErrorMessage(
        this.app.i18n.t('clientHandler.notFoundTitle', {
          name: upperCaseFirst(name),
        }),
        this.app.i18n.t('clientHandler.notFoundTitle', {
          name: name.toLowerCase(),
        })
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
      this.app.i18n.t('clientHandler.networkErrorTitle'),
      this.app.i18n.t('clientHandler.networkErrorDescription')
    )
  }

  /**
   * Returns a standard network error message. For example if the API server
   * could not be reached.
   */
  getTooManyRequestsError() {
    return new ResponseErrorMessage(
      this.app.i18n.t('clientHandler.tooManyRequestsTitle'),
      this.app.i18n.t('clientHandler.tooManyRequestsDescription')
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
      error.handler = new ErrorHandler(
        store,
        app,
        clientErrorMap,
        error.response
      )

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
