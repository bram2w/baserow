<template>
  <div class="grid-view__cell grid-field-link-row__cell active">
    <div class="grid-field-link-row__list">
      <div
        v-for="item in value"
        :key="item.id"
        class="grid-field-link-row__item"
      >
        <span
          class="grid-field-link-row__name"
          :class="{
            'grid-field-link-row__name--unnamed':
              item.value === null || item.value === '',
          }"
        >
          {{ item.value || 'unnamed row ' + item.id }}
        </span>
        <a
          v-if="!readOnly"
          class="grid-field-link-row__remove"
          @click.prevent="removeValue($event, value, item.id)"
        >
          <i class="fas fa-times"></i>
        </a>
      </div>
      <a
        v-if="!readOnly"
        class="grid-field-link-row__item grid-field-link-row__item--link"
        @click.prevent="showModal()"
      >
        <i class="fas fa-plus"></i>
      </a>
    </div>
    <SelectRowModal
      ref="selectModal"
      :table-id="field.link_row_table"
      :value="value"
      @selected="addValue(value, $event)"
      @hidden="hideModal"
    ></SelectRowModal>
  </div>
</template>

<script>
import { isElement } from '@baserow/modules/core/utils/dom'
import gridField from '@baserow/modules/database/mixins/gridField'
import linkRowField from '@baserow/modules/database/mixins/linkRowField'
import SelectRowModal from '@baserow/modules/database/components/row/SelectRowModal'

export default {
  name: 'GridViewFieldLinkRow',
  components: { SelectRowModal },
  mixins: [gridField, linkRowField],
  data() {
    return {
      modalOpen: false,
    }
  },
  methods: {
    select() {
      // While the field is selected we want to open the select row popup by pressing
      // the enter key.
      this.$el.keydownEvent = (event) => {
        if (event.keyCode === 13 && !this.modalOpen) {
          this.showModal()
        }
      }
      document.body.addEventListener('keydown', this.$el.keydownEvent)
    },
    beforeUnSelect() {
      document.body.removeEventListener('keydown', this.$el.keydownEvent)
    },
    /**
     * If the user clicks inside the select row or file modal we do not want to
     * unselect the field. The modals lives in the root of the body element and not
     * inside the cell, so the system naturally wants to unselect when the user clicks
     * inside one of these contexts.
     */
    canUnselectByClickingOutside(event) {
      return !isElement(this.$refs.selectModal.$el, event.target)
    },
    /**
     * Prevent unselecting the field cell by changing the event. Because the deleted
     * item is not going to be part of the dom anymore after deleting it will get
     * noticed as if the user clicked outside the cell which wasn't the case.
     */
    removeValue(event, value, id) {
      event.preventFieldCellUnselect = true
      return linkRowField.methods.removeValue.call(this, event, value, id)
    },
    showModal() {
      if (this.readOnly) {
        return
      }

      this.modalOpen = true
      this.$refs.selectModal.show()
    },
    hideModal() {
      this.modalOpen = false
    },
    /**
     * While the modal is open, all key combinations related to the field must be
     * ignored.
     */
    canKeyDown(event) {
      return !this.modalOpen
    },
    canPaste() {
      return !this.modalOpen
    },
    canCopy() {
      return !this.modalOpen
    },
    canEmpty() {
      return !this.modalOpen
    },
  },
}
</script>
