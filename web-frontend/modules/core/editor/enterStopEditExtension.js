import { Extension } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'

// Please, note that we need to remap Enter to Shift-Enter for every extension
// relying on it in order to emit an event when the user presses Enter.
export const EnterStopEditExtension = Extension.create({
  name: 'enterStopEditHandler',

  addOptions() {
    return {
      shiftKey: false,
    }
  },

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: new PluginKey('enterStopEditHandler'),
        props: {
          handleKeyDown: (view, event) => {
            const { doc } = view.state

            function isDocEmpty() {
              let isEmpty = true
              doc.descendants((node) => {
                const isContent =
                  node.type.name !== 'hardBreak' &&
                  !node.isText &&
                  !node.isBlock
                if (isContent || node.text?.trim()) {
                  isEmpty = false
                }
              })
              return isEmpty
            }

            if (
              event.key === 'Enter' &&
              event.shiftKey === this.options.shiftKey
            ) {
              if (!isDocEmpty()) {
                this.options.vueComponent.$emit('stop-edit')
              }
              return true
            }
            return false
          },
        },
      }),
    ]
  },
})

export default EnterStopEditExtension
