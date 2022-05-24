<template>
  <Modal
    ref="modal"
    :full-height="!!optionalRightSideBar"
    :right-sidebar="!!optionalRightSideBar"
    :content-scrollable="!!optionalRightSideBar"
    :right-sidebar-scrollable="false"
    @hidden="$emit('hidden', { row })"
  >
    <template #content>
      <h2 v-if="primary !== undefined" class="box__title">
        {{ getHeading(primary, row) }}
      </h2>
      <RowEditModalFieldsList
        :primary-is-sortable="primaryIsSortable"
        :fields="visibleFields"
        :sortable="!readOnly"
        :hidden="false"
        :read-only="readOnly"
        :row="row"
        :table="table"
        @field-updated="$emit('field-updated', $event)"
        @field-deleted="$emit('field-deleted')"
        @order-fields="$emit('order-fields', $event)"
        @toggle-field-visibility="$emit('toggle-field-visibility', $event)"
        @update="update"
      ></RowEditModalFieldsList>
      <RowEditModalHiddenFieldsSection
        v-if="hiddenFields.length"
        :show-hidden-fields="showHiddenFields"
        @toggle-hidden-fields-visibility="
          $emit('toggle-hidden-fields-visibility')
        "
      >
        <RowEditModalFieldsList
          :primary-is-sortable="primaryIsSortable"
          :fields="hiddenFields"
          :sortable="false"
          :hidden="true"
          :read-only="readOnly"
          :row="row"
          :table="table"
          @field-updated="$emit('field-updated', $event)"
          @field-deleted="$emit('field-deleted')"
          @toggle-field-visibility="$emit('toggle-field-visibility', $event)"
          @update="update"
        >
        </RowEditModalFieldsList>
      </RowEditModalHiddenFieldsSection>
      <div v-if="!readOnly" class="actions">
        <a
          ref="createFieldContextLink"
          @click="$refs.createFieldContext.toggle($refs.createFieldContextLink)"
        >
          <i class="fas fa-plus"></i>
          {{ $t('rowEditModal.addField') }}
        </a>
        <CreateFieldContext
          ref="createFieldContext"
          :table="table"
          @field-created="$emit('field-created', $event)"
        ></CreateFieldContext>
      </div>
    </template>
    <template v-if="!!optionalRightSideBar" #sidebar>
      <component
        :is="optionalRightSideBar"
        :row="row"
        :read-only="readOnly"
        :table="table"
      ></component>
    </template>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'

import CreateFieldContext from '@baserow/modules/database/components/field/CreateFieldContext'
import RowEditModalFieldsList from './RowEditModalFieldsList.vue'
import RowEditModalHiddenFieldsSection from './RowEditModalHiddenFieldsSection.vue'

export default {
  name: 'RowEditModal',
  components: {
    CreateFieldContext,
    RowEditModalFieldsList,
    RowEditModalHiddenFieldsSection,
  },
  mixins: [modal],
  props: {
    table: {
      type: Object,
      required: true,
    },
    primary: {
      type: Object,
      required: false,
      default: undefined,
    },
    primaryIsSortable: {
      type: Boolean,
      required: false,
      default: false,
    },
    visibleFields: {
      type: Array,
      required: true,
    },
    hiddenFields: {
      type: Array,
      required: false,
      default: () => [],
    },
    showHiddenFields: {
      type: Boolean,
      required: false,
      default: false,
    },
    rows: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      optionalRightSideBar: this.$registry
        .get('application', 'database')
        .getRowEditModalRightSidebarComponent(this.readOnly),
    }
  },
  computed: {
    modalRow() {
      return this.$store.getters['rowModal/get'](this._uid)
    },
    rowId() {
      return this.modalRow.id
    },
    rowExists() {
      return this.modalRow.exists
    },
    row() {
      return this.modalRow.row
    },
  },
  watch: {
    /**
     * It could happen that the view doesn't always have all the rows buffered. When
     * the modal is opened, it will find the correct row by looking through all the
     * rows of the view. If a filter changes, the existing row could be removed from the
     * buffer while the user still wants to edit the row because the modal is open. In
     * that case, we will keep a copy in the `rowModal` store, which will also listen
     * for real time update events to make sure the latest information is always
     * visible. If the buffer of the view changes and the row does exist, we want to
     * switch to that version to maintain reactivity between the two.
     */
    rows(value) {
      const row = value.find((r) => r !== null && r.id === this.rowId)
      if (row === undefined && this.rowExists) {
        this.$store.dispatch('rowModal/doesNotExist', {
          componentId: this._uid,
        })
      } else if (row !== undefined && !this.rowExists) {
        this.$store.dispatch('rowModal/doesExist', {
          componentId: this._uid,
          row,
        })
      } else if (row !== undefined) {
        // If the row already exists and it has changed, we need to replace it,
        // otherwise we might loose reactivity.
        this.$store.dispatch('rowModal/replace', {
          componentId: this._uid,
          row,
        })
      }
    },
  },
  methods: {
    show(rowId, rowFallback = {}, ...args) {
      const row = this.rows.find((r) => r !== null && r.id === rowId)
      this.$store.dispatch('rowModal/open', {
        tableId: this.table.id,
        componentId: this._uid,
        id: rowId,
        row: row || rowFallback,
        exists: !!row,
      })
      this.getRootModal().show(...args)
    },
    hide(...args) {
      this.$store.dispatch('rowModal/clear', { componentId: this._uid })
      this.getRootModal().hide(...args)
    },
    /**
     * Because the modal can't update values by himself, an event will be called to
     * notify the parent component to actually update the value.
     */
    update(context) {
      context.table = this.table
      this.$emit('update', context)
    },
    getHeading(primary, row) {
      const name = `field_${primary.id}`
      if (Object.prototype.hasOwnProperty.call(row, name)) {
        return this.$registry
          .get('field', primary.type)
          .toHumanReadableString(primary, row[name])
      } else {
        return null
      }
    },
  },
}
</script>
