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
      <RowEditModalField
        v-for="field in getFields(fields, primary)"
        :key="'row-edit-field-' + field.id"
        :ref="'field-' + field.id"
        :field="field"
        :read-only="readOnly"
        :row="row"
        :table="table"
        @update="update"
        @field-updated="$emit('field-updated', $event)"
        @field-deleted="$emit('field-deleted')"
      ></RowEditModalField>
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
          @refresh="$emit('refresh', $event)"
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
import { mapGetters } from 'vuex'

import modal from '@baserow/modules/core/mixins/modal'
import RowEditModalField from '@baserow/modules/database/components/row/RowEditModalField'
import CreateFieldContext from '@baserow/modules/database/components/field/CreateFieldContext'

export default {
  name: 'RowEditModal',
  components: {
    RowEditModalField,
    CreateFieldContext,
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
    fields: {
      type: Array,
      required: true,
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
    ...mapGetters({
      rowId: 'rowModal/id',
      rowExists: 'rowModal/exists',
      row: 'rowModal/row',
    }),
  },
  watch: {
    /**
     * It could happen that the view doesn't always have all the rows buffered. When
     * the modal is opened, it will find the correct row by looking through all the
     * rows of the view. If a filter changes, the existing row could be removed the
     * buffer while the user still wants to edit the row because the modal is open. In
     * that case, we will keep a copy in the `rowModal` store, which will also listen
     * for real time update events to make sure the latest information is always
     * visible. If the buffer of the view changes and the row does exist, we want to
     * switch to that version to maintain reactivity between the two.
     */
    rows(value) {
      const row = value.find((r) => r !== null && r.id === this.rowId)
      if (row === undefined && this.rowExists) {
        this.$store.dispatch('rowModal/doesNotExist')
      } else if (row !== undefined && !this.rowExists) {
        this.$store.dispatch('rowModal/doesExist', { row })
      }
    },
  },
  methods: {
    show(rowId, ...args) {
      const row = this.rows.find((r) => r !== null && r.id === rowId)
      this.$store.dispatch('rowModal/open', {
        id: rowId,
        row: row || {},
        exists: !!row,
      })
      this.getRootModal().show(...args)
    },
    hide(...args) {
      this.$store.dispatch('rowModal/clear')
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
    getFields(fields, primary) {
      return (primary !== undefined ? [primary].concat(fields) : fields)
        .slice()
        .sort((a, b) => a.order - b.order)
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
