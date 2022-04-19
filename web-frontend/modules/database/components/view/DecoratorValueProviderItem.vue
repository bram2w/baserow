<template functional>
  <div class="value-provider-item">
    <div class="value-provider-item__title">
      <i
        :class="`fa fa-fw fa-${props.valueProviderType.getIconClass()} value-provider-item__icon`"
      />
      {{ props.valueProviderType.getName() }}
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
