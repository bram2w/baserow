import { isSecureURL } from '@baserow/modules/core/utils/string'

export class RealTimeHandler {
  constructor(context) {
    this.context = context
    this.socket = null
    this.connected = false
    this.reconnect = false
    this.reconnectTimeout = null
    this.events = {}
    this.attempts = 0
    this.page = null
    this.pageParameters = {}
    this.subscribedToPage = true
    this.lastToken = null
    this.authenticationSuccess = true
    this.registerCoreEvents()
  }

  /**
   * Creates a new connection with to the web socket so that real time updates can be
   * received.
   */
  connect(reconnect = true) {
    this.reconnect = reconnect

    const token = this.context.store.getters['auth/token']

    // If the user is already connected to the web socket, we don't have to do
    // anything.
    if (this.connected) {
      return
    }

    // Check if we already had a failed authentication response from the server before.
    // If so, and if the authentication token has not changed, we don't need to connect
    // because we already know it will fail.
    if (!this.authenticationSuccess && token === this.lastToken) {
      this.delayedReconnect()
      return
    }

    this.lastToken = token

    // The web socket url is the same as the PUBLIC_BACKEND_URL apart from the
    // protocol.
    const rawUrl = this.context.app.$env.PUBLIC_BACKEND_URL
    const url = new URL(rawUrl)
    url.protocol = isSecureURL(rawUrl) ? 'wss:' : 'ws:'
    url.pathname = '/ws/core/'

    this.socket = new WebSocket(`${url}?jwt_token=${token}`)
    this.socket.onopen = () => {
      this.context.store.dispatch('notification/setConnecting', false)
      this.connected = true
      this.attempts = 0

      // If the client needs to be subscribed to a page we can do that directly
      // after connecting.
      if (!this.subscribedToPage) {
        this.subscribeToPage()
      }
    }

    /**
     * The received messages are always JSON so we need to the parse it, extract the
     * type and call the correct event.
     */
    this.socket.onmessage = (message) => {
      let data = {}

      try {
        data = JSON.parse(message.data)
      } catch {
        return
      }

      if (
        Object.prototype.hasOwnProperty.call(data, 'type') &&
        Object.prototype.hasOwnProperty.call(this.events, data.type)
      ) {
        this.events[data.type](this.context, data)
      }
    }

    /**
     * When the connection closes we want to reconnect immediately because we don't
     * want to miss any important real time updates. After the first attempt we want to
     * delay retry with 5 seconds.
     */
    this.socket.onclose = (event) => {
      this.connected = false
      // By default the user not subscribed to a page a.k.a `null`, so if the current
      // page is already null we can mark it as subscribed.
      this.subscribedToPage = this.page === null

      // Automatically reconnect after the given timeout if the socket closes not
      // normally.
      // 1000=CLOSE_NORMAL
      // 1001=CLOSE_GOING_AWAY
      // 1002+=an error.
      if (event.code > 1001) {
        this.delayedReconnect()
      }
    }
  }

  /**
   * If reconnecting is enabled then a timeout is created that will try to connect
   * to the backend one more time.
   */
  delayedReconnect() {
    if (!this.reconnect) {
      return
    }

    this.attempts++
    this.context.store.dispatch('notification/setConnecting', true)

    this.reconnectTimeout = setTimeout(
      () => {
        this.connect(true)
      },
      // After the first try, we want to try again every 5 seconds.
      this.attempts > 1 ? 5000 : 0
    )
  }

  /**
   * Subscribes the client to a given page. After subscribing the client will
   * receive updated related to that page. This is for example used when a user
   * opens a table page.
   */
  subscribe(page, parameters) {
    this.page = page
    this.pageParameters = parameters
    this.subscribedToPage = false

    // If the client is already connected we can directly subscribe to the page.
    if (this.connected) {
      this.subscribeToPage()
    }
  }

  /**
   * Sends a request to the real time server that updates for a certain page +
   * parameters must be received.
   */
  subscribeToPage() {
    this.socket.send(
      JSON.stringify({
        page: this.page === null ? '' : this.page,
        ...this.pageParameters,
      })
    )
    this.subscribedToPage = true
  }

  /**
   * Disconnects the socket and resets all the variables. The can be used when
   * navigating to another page that doesn't require updates.
   */
  disconnect() {
    if (this.connected) {
      this.socket.close()
    }

    this.context.store.dispatch('notification/setConnecting', false)
    clearTimeout(this.reconnectTimeout)
    this.reconnect = false
    this.attempts = 0
    this.connected = false
  }

  /**
   * Registers a new event with the event registry.
   */
  registerEvent(type, callback) {
    this.events[type] = callback
  }

  /**
   * Registers all the core event handlers, which is for the groups and applications.
   */
  registerCoreEvents() {
    // When the authentication is successful we want to store the web socket id in
    // auth store. Every AJAX request will include the web socket id as header, this
    // way the backend knows that this client does not has to receive the event
    // because we already know about the change.
    this.registerEvent('authentication', ({ store }, data) => {
      store.dispatch('auth/setWebSocketId', data.web_socket_id)

      // Store if the authentication was successful in order to prevent retries that
      // will fail.
      this.authenticationSuccess = data.success
    })

    this.registerEvent('group_created', ({ store }, data) => {
      store.dispatch('group/forceCreate', data.group)
    })

    this.registerEvent('group_updated', ({ store }, data) => {
      const group = store.getters['group/get'](data.group_id)
      if (group !== undefined) {
        store.dispatch('group/forceUpdate', { group, values: data.group })
      }
    })

    this.registerEvent('group_deleted', ({ store }, data) => {
      const group = store.getters['group/get'](data.group_id)
      if (group !== undefined) {
        store.dispatch('group/forceDelete', group)
      }
    })

    this.registerEvent('application_created', ({ store }, data) => {
      store.dispatch('application/forceCreate', data.application)
    })

    this.registerEvent('application_updated', ({ store }, data) => {
      const application = store.getters['application/get'](data.application_id)
      if (application !== undefined) {
        store.dispatch('application/forceUpdate', {
          application,
          data: data.application,
        })
      }
    })

    this.registerEvent('application_deleted', ({ store }, data) => {
      const application = store.getters['application/get'](data.application_id)
      if (application !== undefined) {
        store.dispatch('application/forceDelete', application)
      }
    })
  }
}

export default function (context, inject) {
  inject('realtime', new RealTimeHandler(context))
}
