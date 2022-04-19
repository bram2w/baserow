<template functional>
  <div class="decorator-item">
    <img class="decorator-item__image" :src="props.decoratorType.getImage()" />
    <div class="decorator-item__content">
      <div class="decorator-item__title">
        {{ props.decoratorType.getName() }}
      </div>
      <div class="decorator-item__description">
        {{ props.decoratorType.getDescription() }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ViewDecoratorItem',
  props: {
    decoratorType: {
      type: Object,
      required: true,
    },
  },
}
</script>
