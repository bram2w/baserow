<template>
  <Modal>
    <h2 v-if="primary !== undefined" class="box__title">
      {{ getHeading(primary, row) }}
    </h2>
    <form>
      <RowEditModalField
        v-for="field in getFields(fields, primary)"
        :ref="'field-' + field.id"
        :key="'row-edit-field-' + field.id"
        :field="field"
        :row="row"
        @update="update"
      ></RowEditModalField>
      <div class="actions">
        <a
          ref="createFieldContextLink"
          @click="$refs.createFieldContext.toggle($refs.createFieldContextLink)"
        >
          <i class="fas fa-plus"></i>
          add field
        </a>
        <CreateFieldContext
          ref="createFieldContext"
          :table="table"
        ></CreateFieldContext>
      </div>
    </form>
  </Modal>
</template>

<script>
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
  },
  data() {
    return {
      row: {},
    }
  },
  methods: {
    show(row, ...args) {
      this.row = row
      this.getRootModal().show(...args)
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
      return primary !== undefined ? [primary].concat(fields) : fields
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
