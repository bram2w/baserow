import { Image } from '@tiptap/extension-image'

export const ScalableImage = Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      maxWidth: {
        default: '100%',
        renderHTML: (attributes) => {
          return {
            style: `max-width: ${attributes.maxWidth}; height: auto;`,
          }
        },
      },
    }
  },
})
