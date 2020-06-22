<template>
  <div class="grid-view__column">
    <div
      class="grid-view__description"
      :class="{ 'grid-view__description--loading': field._.loading }"
    >
      <div class="grid-view__description-icon">
        <i class="fas" :class="'fa-' + field._.type.iconClass"></i>
      </div>
      <div class="grid-view__description-name">{{ field.name }}</div>
      <a
        ref="contextLink"
        class="grid-view__description-options"
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
