<template>
  <div
    class="value-provider-list"
    :class="{
      [`value-provider-list--${direction}`]: true,
      'value-provider-list--read-only': readOnly,
    }"
  >
    <div
      v-for="valueProviderType in availableValueProviderTypes"
      :key="valueProviderType.getType()"
      class="value-provider-list__item"
      :class="{
        'value-provider-list__item--selected':
          valueProviderType.getType() === decoration.value_provider_type,
      }"
      @click="!readOnly && $emit('select', valueProviderType.getType())"
    >
      <DecoratorValueProviderItem :value-provider-type="valueProviderType" />
    </div>
  </div>
</template>

<script>
import DecoratorValueProviderItem from '@baserow/modules/database/components/view/DecoratorValueProviderItem'

export default {
  name: 'DecoratorValueProviderList',
  components: { DecoratorValueProviderItem },
  props: {
    decoration: {
      type: Object,
      required: true,
    },
    direction: {
      type: String,
      required: false,
      default: 'column',
    },
    readOnly: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    availableValueProviderTypes() {
      const decorationType = this.$registry.get(
        'viewDecorator',
        this.decoration.type
      )
      return this.$registry
        .getOrderedList('decoratorValueProvider')
        .filter((valueProviderType) =>
          valueProviderType.isCompatible(decorationType)
        )
    },
  },
}
</script>
