import { isCharacterKeyPress } from '@baserow/modules/core/utils/events'

/**
 * This mixin can be used with a grid view field if the field only needs an input. For
 * example for the text and number fields. It depends on the gridField mixin.
 */
export default {
  data() {
    return {
      /**
       * Indicates whether of the user is editing the value.
       */
      editing: false,
      /**
       *  A temporary copy of the value when editing.
       */
      copy: null,
    }
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
        // If the enter key is pressed.
        if (event.keyCode === 13) {
          if (this.editing) {
            // While editing we want to save the changes.
            this.save()
          } else {
            // If only selected we will start the editing mode.
            this.edit()
          }
        } else if (!this.editing && isCharacterKeyPress(event)) {
          // If another key was pressed while not editing we want to replace the
          // exiting value with something new.
          this.edit('')
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
      if (this.editing) {
        this.save()
      }
      document.body.removeEventListener('keydown', this.$el.keydownEvent)
    },
    /**
     * Event that is called when the user double clicks in the column. In this case
     * we want to initiate the editing mode.
     */
    doubleClick() {
      this.edit()
    },
    /**
     * Method that can be called to initiate the edit state.
     */
    edit(value = null) {
      this.editing = true
      this.copy = value === null ? this.value : value
      this.afterEdit()
    },
    /**
     * Method that can be called when in the editing state. It will bring the
     * component outside of the editing state and will emit an event which will
     * eventually save the changes.
     */
    save() {
      this.editing = false

      // If the value hasn't changed we don't want to do anything.
      if (this.copy === this.value) {
        return
      }

      this.$emit('update', this.copy, this.value)
      this.afterSave()
    },
    /**
     * Method that is called after initiating the edit state. This can be overridden
     * in the component.
     */
    afterEdit() {},
    /**
     * Method that is called after saving the value. This can be overridden in the
     * component.
     */
    afterSave() {},
  },
}
