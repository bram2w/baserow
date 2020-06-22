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
          :field="field"
          @update="$refs.context.hide()"
        ></UpdateFieldContext>
      </li>
      <li v-if="!field.primary">
        <a @click="deleteField(field)">
          <i class="context__menu-icon fas fa-fw fa-trash"></i>
          Delete field
        </a>
      </li>
    </ul>
  </Context>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import context from '@baserow/modules/core/mixins/context'
import UpdateFieldContext from '@baserow/modules/database/components/field/UpdateFieldContext'

export default {
  name: 'FieldContext',
  components: { UpdateFieldContext },
  mixins: [context],
  props: {
    field: {
      type: Object,
      required: true,
    },
  },
  methods: {
    setLoading(field, value) {
      this.$store.dispatch('field/setItemLoading', { field, value })
    },
    async deleteField(field) {
      this.$refs.context.hide()
      this.setLoading(field, true)

      try {
        await this.$store.dispatch('field/delete', field)
      } catch (error) {
        notifyIf(error, 'field')
      }

      this.setLoading(field, false)
    },
  },
}
</script>
