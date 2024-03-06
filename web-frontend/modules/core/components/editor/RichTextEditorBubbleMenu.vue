<template>
  <FloatingMenu
    v-if="editor"
    :editor="editor"
    :should-show="() => true"
    :tippy-options="{
      duration: 250,
      placement: 'top',
      offset: [0, -5],
    }"
  >
    <ul class="rich-text-editor__bubble-menu">
      <li
        :title="$t('richTextEditorBubbleMenu.bold')"
        class="rich-text-editor__bubble-menu-button"
      >
        <button
          :class="{ 'is-active': editor.isActive('bold') }"
          @click="editor.chain().focus().toggleBold().run()"
        >
          <i class="iconoir-bold"></i>
        </button>
      </li>
      <li
        :title="$t('richTextEditorBubbleMenu.italic')"
        class="rich-text-editor__bubble-menu-button"
      >
        <button
          :class="{ 'is-active': editor.isActive('italic') }"
          @click="editor.chain().focus().toggleItalic().run()"
        >
          <i class="iconoir-italic"></i>
        </button>
      </li>
      <li
        :title="$t('richTextEditorBubbleMenu.underline')"
        class="rich-text-editor__bubble-menu-button"
      >
        <button
          :class="{ 'is-active': editor.isActive('underline') }"
          @click="editor.chain().focus().toggleUnderline().run()"
        >
          <i class="iconoir-underline"></i>
        </button>
      </li>
      <li
        :title="$t('richTextEditorBubbleMenu.strikethrough')"
        class="rich-text-editor__bubble-menu-button"
      >
        <button
          :class="{ 'is-active': editor.isActive('strike') }"
          @click="editor.chain().focus().toggleStrike().run()"
        >
          <i class="iconoir-strikethrough"></i>
        </button>
      </li>
    </ul>
  </FloatingMenu>
</template>

<script>
import { FloatingMenu } from '@tiptap/vue-2'
import { isElement } from '@baserow/modules/core/utils/dom'

export default {
  name: 'RichTextEditorBubbleMenu',
  components: {
    FloatingMenu,
  },
  props: {
    editor: {
      type: Object,
      required: false,
      default: null,
    },
  },
  methods: {
    isEventTargetInside(event) {
      return (
        isElement(this.$el, event.target) ||
        isElement(this.$el, event.relatedTarget)
      )
    },
  },
}
</script>
