<template>
  <div
    :key="elementType.name"
    v-tooltip="disallowedTypeForAncestry ? disabledElementMessage : null"
    class="add-element-card"
    :class="{ 'add-element-card--disabled': disabled }"
    v-on="$listeners"
  >
    <div v-if="loading" class="loading"></div>
    <template v-else>
      <div class="add-element-card__element-type">
        <i
          class="add-element-card__element-type-icon"
          :class="elementType.iconClass"
        ></i>
        <span>{{ elementType.name }}</span>
      </div>
      <div class="margin-top-1 add-element-card__description">
        {{ elementType.description }}
      </div>
    </template>
  </div>
</template>

<script>
export default {
  name: 'AddElementCard',
  props: {
    elementType: {
      type: Object,
      required: true,
    },
    parentType: {
      type: Object,
      required: false,
      default: null,
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
    disallowedTypeForAncestry: {
      type: Boolean,
      required: false,
      default: false,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    disabledElementMessage() {
      return this.$t('addElementModal.disabledElementTooltip')
    },
  },
}
</script>
