<template>
  <CreateFieldContext
    ref="createFieldContext"
    :table="table"
    :force-typed="forcedType"
    :use-action-group-id="true"
    @field-created="$emit('field-created', $event)"
    @field-created-callback-done="updateInsertedFieldOrder"
  ></CreateFieldContext>
</template>

<script>
import CreateFieldContext from '@baserow/modules/database/components/field/CreateFieldContext'

export default {
  name: 'InsertFieldContext',
  components: { CreateFieldContext },

  props: {
    table: {
      type: Object,
      required: true,
    },
    forcedType: {
      type: [String, null],
      required: false,
      default: null,
    },
    fromField: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      position: 'left', // left or right
    }
  },
  methods: {
    updateInsertedFieldOrder({ newField, undoRedoActionGroupId }) {
      // GridViewHead will update the order of the fields and call the backend endpoint
      this.$emit('move-field', {
        newField,
        position: this.position,
        fromField: this.fromField,
        undoRedoActionGroupId,
      })
    },
    toggle(ref, position) {
      // avoid changing the position in the middle of a fields creation
      if (this.$refs.createFieldContext.loading) {
        return
      }

      this.position = position
      const popupAnchor = position === 'left' ? 'right' : 'left'
      this.$refs.createFieldContext.toggle(ref, 'bottom', popupAnchor, 0)
    },
  },
}
</script>
