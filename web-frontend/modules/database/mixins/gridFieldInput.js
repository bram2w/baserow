import { isPrintableUnicodeCharacterKeyPress } from '@baserow/modules/core/utils/events'

/**
 * This mixin can be used with a grid view field if the field only needs an input. For
 * example for the text and number fields. It depends on the gridField mixin.
 */
export default {
  data() {
    return {
      /**
       * Indicates whether the user is editing the value.
       */
      editing: false,
      /**
       * A temporary copy of the value when editing.
       */
      copy: null,
    }
  },
  watch: {
    copy(value) {
      if (this.editing) {
        this.$emit('edit', value, this.value)
      }
    },
  },
  methods: {
    /**
     * Event that is called when the column is selected. Here we will add an event
     * keydown event listener so we monitor if the enter key is pressed which should
     * start the editing or save the current changes. We also look check if other
     * characters are pressed because that should replace the value.
     */
    select() {
      this.$el.keydownEvent = (event) => {
        // If the tab or arrow keys are pressed we don't want to do anything because
        // the GridViewField component will select the next field.
        const ignoredKeys = [9, 37, 38, 39, 40]
        if (ignoredKeys.includes(event.keyCode)) {
          return
        }

        // If the escape key is pressed while editing we want to cancel the current
        // input and undo the editing state.
        if (event.keyCode === 27 && this.editing) {
          this.cancel()
          return
        }

        // If the enter key is pressed.
        if (event.keyCode === 13) {
          if (
            this.editing &&
            this.isValid() &&
            this.canSaveByPressingEnter(event)
          ) {
            // While editing we want to save the changes.
            this.save()
          } else if (!this.editing) {
            // If only selected we will start the editing mode.
            this.edit(null, event)
          }
        }

        // If F2 is pressed we want to switch into editing mode
        // with the current value of the cell
        if (event.key === 'F2' && !this.editing) {
          this.edit(null, event)
        }

        // If a printable key was pressed while not editing we want to replace the
        // exiting value with something new.
        if (!this.editing && isPrintableUnicodeCharacterKeyPress(event)) {
          this.edit('', event)
        }
      }
      document.body.addEventListener('keydown', this.$el.keydownEvent)
    },
    /**
     * Event that is called wen the column is unselected, for example when clicked
     * outside. Here we will remove the added keydown event because we don't longer
     * need it. We will also save the changes if the user was editing.
     */
    beforeUnSelect() {
      if (this.editing && this.isValid()) {
        this.save()
      } else {
        this.editing = false
      }
      document.body.removeEventListener('keydown', this.$el.keydownEvent)
    },
    /**
     * Event that is called when the user double clicks in the column. In this case
     * we want to initiate the editing mode.
     */
    doubleClick(event = null) {
      if (!this.editing) {
        this.edit(null, event)
      }
    },
    /**
     * Method that can be called to initiate the edit state.
     */
    edit(value = null, event = null) {
      if (this.readOnly) {
        return
      }

      this.editing = true
      this.copy = value === null ? this.value : value
      this.afterEdit(event)
    },
    /**
     * Method that can be called when in the editing state. It will bring the
     * component outside of the editing state and will emit an event which will
     * eventually save the changes.
     */
    save() {
      this.editing = false
      const newValue = this.beforeSave(this.copy)

      // If the value hasn't changed we don't want to do anything.
      if (newValue === this.value) {
        return
      }

      this.$emit('update', newValue, this.value)
      this.afterSave()
    },
    /**
     * Cancels the current editing state and reverts the copy to the old value
     * without saving.
     */
    cancel() {
      this.editing = false
      this.copy = this.value
      this.$emit('edit', this.value, this.value)
    },
    /**
     * Method that is called after initiating the edit state. This can be overridden
     * in the component.
     */
    afterEdit() {},
    /**
     * This method is called before saving the value. Optionally the value can be
     * changed or formatted here if necessary.
     */
    beforeSave(value) {
      return value
    },
    /**
     * Method that is called after saving the value. This can be overridden in the
     * component.
     */
    afterSave() {},
    /**
     * Small helper method that stops the propagation of the context menu when the
     * field is being edited. Can be used on the element like:
     * `@contextmenu="stopContextIfEditing($event)"`.
     */
    stopContextIfEditing(event) {
      if (this.editing) {
        event.stopPropagation()
      }
    },
    /**
     * While editing we want to disable the arrow keys to select the next of
     * previous field. The tab key stays enabled.
     */
    canSelectNext(event) {
      const arrowKeys = [37, 38, 39, 40]
      return !this.editing || !arrowKeys.includes(event.keyCode)
    },
    /**
     * If true the value can be saved by pressing the enter key. This could for
     * example be disabled for a long text field that can have multiple lines.
     */
    canSaveByPressingEnter(event) {
      return true
    },
    canCopy() {
      return !this.editing
    },
    canPaste() {
      return !this.editing
    },
    canEmpty() {
      return !this.editing
    },
    getError() {
      return this.getValidationError(this.editing ? this.copy : this.value)
    },
  },
}
