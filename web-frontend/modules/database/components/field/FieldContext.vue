<template>
  <Context ref="context">
    <ul class="context__menu">
      <li>
        <a
          ref="updateFieldContextLink"
          class="grid-view__description-options"
          @click="
            $refs.updateFieldContext.toggle(
              $refs.updateFieldContextLink,
              'bottom',
              'left',
              0
            )
          "
        >
          <i class="context__menu-icon fas fa-fw fa-pen"></i>
          Edit field
        </a>
        <UpdateFieldContext
          ref="updateFieldContext"
          :table="table"
          :field="field"
          @update="$emit('update', $event)"
          @updated="$refs.context.hide()"
        ></UpdateFieldContext>
      </li>
      <slot></slot>
      <li v-if="!field.primary">
        <a @click="deleteField()">
          <i class="context__menu-icon fas fa-fw fa-trash"></i>
          Delete field
        </a>
      </li>
    </ul>
    <DeleteFieldModal
      v-if="!field.primary"
      ref="deleteFieldModal"
      :field="field"
      @delete="$emit('delete')"
    />
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import UpdateFieldContext from '@baserow/modules/database/components/field/UpdateFieldContext'
import DeleteFieldModal from './DeleteFieldModal'

export default {
  name: 'FieldContext',
  components: {
    UpdateFieldContext,
    DeleteFieldModal,
  },
  mixins: [context],
  props: {
    table: {
      type: Object,
      required: true,
    },
    field: {
      type: Object,
      required: true,
    },
  },
  methods: {
    setLoading(field, value) {
      this.$store.dispatch('field/setItemLoading', { field, value })
    },
    deleteField() {
      this.$refs.context.hide()
      this.$refs.deleteFieldModal.show()
    },
  },
}
</script>
