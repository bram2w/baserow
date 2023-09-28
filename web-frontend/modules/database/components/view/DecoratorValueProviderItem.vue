<template functional>
  <div class="value-provider-item">
    <div class="value-provider-item__title">
      <i
        :class="`${props.valueProviderType.getIconClass()} value-provider-item__icon`"
      />
      <span class="value-provider-item__title-text">{{
        props.valueProviderType.getName()
      }}</span>
    </div>
    <div class="value-provider-item__description">
      {{ props.valueProviderType.getDescription() }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'ViewDecoratorItem',
  props: {
    valueProviderType: {
      type: Object,
      required: true,
    },
  },
}
</script>
