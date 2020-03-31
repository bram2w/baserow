/**
 * This mixin works the best in combination with the Error component.
 */
export default {
  data() {
    return {
      error: {
        visible: false,
        title: '',
        message: '',
      },
    }
  },
  methods: {
    /**
     * Can be called after catching an error. If an handler is available the error
     * data is populated with the correct error message.
     */
    handleError(error, name, specificErrorMap = null) {
      if (error.handler) {
        const message = error.handler.getMessage(name, specificErrorMap)
        this.showError(message)
        error.handler.handled()
      } else {
        throw error
      }
    },
    /**
     * Populates the error data with the provided message. Can be called with an
     * error message object or with a title and message.
     */
    showError(title, message = null) {
      this.error.visible = true

      if (message === null) {
        this.error.title = title.title
        this.error.message = title.message
      } else {
        this.error.title = title
        this.error.message = message
      }
    },
    hideError() {
      this.error.visible = false
    },
  },
}
