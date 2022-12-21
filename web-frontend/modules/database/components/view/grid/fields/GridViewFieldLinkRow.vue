<template>
  <div class="grid-view__cell grid-field-many-to-many__cell active">
    <div class="grid-field-many-to-many__list">
      <component
        :is="publicGrid || !canAccessLinkedTable ? 'span' : 'a'"
        v-for="item in value"
        :key="item.id"
        class="grid-field-many-to-many__item"
        @click.prevent="showForeignRowModal(item)"
      >
        <span
          class="grid-field-many-to-many__name"
          :class="{
            'grid-field-link-row__unnamed':
              item.value === null || item.value === '',
          }"
        >
          {{
            item.value || $t('gridViewFieldLinkRow.unnamed', { value: item.id })
          }}
        </span>
        <span
          v-if="itemLoadingId === item.id"
          class="grid-field-many-to-many__loading"
        ></span>
        <a
          v-else-if="canAccessLinkedTable"
          class="grid-field-many-to-many__remove"
          @click.prevent.stop="removeValue($event, value, item.id)"
        >
          <i class="fas fa-times"></i>
        </a>
      </component>
      <a
        v-if="canAccessLinkedTable"
        class="
          grid-field-many-to-many__item grid-field-many-to-many__item--link
        "
        @click.prevent="showModal()"
      >
        <i class="fas fa-plus"></i>
      </a>
    </div>
    <SelectRowModal
      v-if="canAccessLinkedTable"
      ref="selectModal"
      :table-id="field.link_row_table_id"
      :value="value"
      @selected="addValue(value, $event)"
      @hidden="hideModal"
    ></SelectRowModal>
    <ForeignRowEditModal
      v-if="canAccessLinkedTable"
      ref="rowEditModal"
      :table-id="field.link_row_table_id"
      @hidden="hideModal"
    ></ForeignRowEditModal>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import { isElement } from '@baserow/modules/core/utils/dom'
import gridField from '@baserow/modules/database/mixins/gridField'
import linkRowField from '@baserow/modules/database/mixins/linkRowField'
import SelectRowModal from '@baserow/modules/database/components/row/SelectRowModal'
import ForeignRowEditModal from '@baserow/modules/database/components/row/ForeignRowEditModal'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'

export default {
  name: 'GridViewFieldLinkRow',
  components: { ForeignRowEditModal, SelectRowModal },
  mixins: [gridField, linkRowField],
  inject: {
    group: { default: null },
  },
  data() {
    return {
      modalOpen: false,
      itemLoadingId: -1,
    }
  },
  computed: {
    canAccessLinkedTable() {
      const linkedTable = this.allTables.find(
        ({ id }) => id === this.field.link_row_table_id
      )

      if (!linkedTable) {
        return false
      }

      return (
        this.$hasPermission(
          'database.table.read',
          linkedTable,
          this.group.id
        ) && !this.readOnly
      )
    },
    allTables() {
      const databaseType = DatabaseApplicationType.getType()
      return this.$store.getters['application/getAll'].reduce(
        (tables, application) => {
          if (application.type === databaseType) {
            return tables.concat(application.tables || [])
          }
          return tables
        },
        []
      )
    },
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        publicGrid: 'page/view/public/getIsPublic',
      }),
    }
  },
  methods: {
    select() {
      // While the field is selected we want to open the select row popup by pressing
      // the enter key.
      this.$el.keydownEvent = (event) => {
        if (event.key === 'Enter' && !this.modalOpen) {
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
      if (!this.canAccessLinkedTable) {
        return true
      }

      const openModals = [
        ...this.$refs.selectModal.$refs.modal.moveToBody.children.map(
          (child) => child.$el
        ),
        this.$refs.selectModal.$el,
        this.$refs.rowEditModal.$refs.modal.$el,
      ]

      return !openModals.some((modal) => {
        return isElement(modal, event.target)
      })
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
      if (!this.canAccessLinkedTable) {
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
    canKeyDown() {
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
    async showForeignRowModal(item) {
      // It's not possible to open the related row when the view is shared publicly
      // because the visitor doesn't have the right permissions.
      if (this.publicGrid || !this.canAccessLinkedTable) {
        return
      }

      this.itemLoadingId = item.id
      try {
        await this.$refs.rowEditModal.show(item.id)
        this.modalOpen = true
      } catch (error) {
        notifyIf(error)
      }
      this.itemLoadingId = -1
    },
  },
}
</script>
