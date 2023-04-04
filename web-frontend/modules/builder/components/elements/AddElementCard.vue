<template>
  <div
    class="add-element-card"
    :class="{ 'add-element-card--disabled': disabled }"
    v-on="$listeners"
  >
    <div v-if="loading" class="loading"></div>
    <template v-else>
      <div>
        <i :class="`fas fa-${elementType.iconClass}`"></i>
        <span class="margin-left-1">{{ elementType.name }}</span>
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
    loading: {
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
}
</script>
