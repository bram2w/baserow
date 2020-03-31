<template>
  <div class="grid-view-column" style="width: 200px;">
    <div
      class="grid-view-description"
      :class="{ 'grid-view-description-loading': field._.loading }"
    >
      <div class="grid-view-description-icon">
        <i class="fas" :class="'fa-' + field._.type.iconClass"></i>
      </div>
      <div class="grid-view-description-name">{{ field.name }}</div>
      <a
        ref="contextLink"
        class="grid-view-description-options"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
      >
        <i class="fas fa-caret-down"></i>
      </a>
      <Context ref="context">
        <ul class="context-menu">
          <li>
            <a
              ref="updateFieldContextLink"
              class="grid-view-description-options"
              @click="
                $refs.updateFieldContext.toggle(
                  $refs.updateFieldContextLink,
                  'bottom',
                  'right',
                  0
                )
              "
            >
              <i class="context-menu-icon fas fa-fw fa-pen"></i>
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
              <i class="context-menu-icon fas fa-fw fa-trash"></i>
              Delete field
            </a>
          </li>
        </ul>
      </Context>
    </div>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import UpdateFieldContext from '@baserow/modules/database/components/field/UpdateFieldContext'

export default {
  name: 'GridViewFieldType',
  components: { UpdateFieldContext },
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
