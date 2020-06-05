<template>
  <div class="grid-view-column">
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
      <FieldContext ref="context" :field="field"></FieldContext>
      <slot></slot>
    </div>
  </div>
</template>

<script>
import FieldContext from '@baserow/modules/database/components/field/FieldContext'

export default {
  name: 'GridViewFieldType',
  components: { FieldContext },
  props: {
    field: {
      type: Object,
      required: true,
    },
  },
}
</script>
