<template>
  <Modal :tiny="true" :close-button="false">
    <h3>
      Are you sure you want to
      {{ selectedIsTrashed ? 'permanently delete' : 'empty the trash of' }}
      {{ name }}?
    </h3>
    <p>
      This will permanently delete
      {{
        selectedIsTrashed ? 'it and all of its contents' : 'the listed items'
      }}. After which they cannot be recovered.
    </p>
    <div class="actions">
      <ul class="action__links">
        <li>
          <a @click.prevent="hide()">Cancel</a>
        </li>
      </ul>
      <a class="button button button--error" @click.prevent="emitEmptyAndClose">
        {{ selectedIsTrashed ? 'Permanently delete' : 'Empty' }}
      </a>
    </div>
  </Modal>
</template>

<script>
/**
 * A simple confirmation modal to check that the user is sure they want to permanently
 * delete / empty.
 */
import modal from '@baserow/modules/core/mixins/modal'

export default {
  name: 'TrashEmptyModal',
  components: {},
  mixins: [modal],
  props: {
    name: {
      type: String,
      required: true,
    },
    selectedIsTrashed: {
      type: Boolean,
      required: true,
    },
  },
  methods: {
    emitEmptyAndClose() {
      this.$emit('empty')
      this.hide()
    },
  },
}
</script>
