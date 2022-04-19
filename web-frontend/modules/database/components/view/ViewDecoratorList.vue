<template>
  <div class="decorator-list">
    <div
      v-for="decoratorType in viewDecoratorTypes"
      :key="decoratorType.getType()"
      v-tooltip="getTooltip(decoratorType)"
      class="decorator-list__item"
      :class="{ 'decorator-list__item--disabled': isDisabled(decoratorType) }"
      @click="addDecoration(decoratorType)"
    >
      <ViewDecoratorItem :decorator-type="decoratorType" />
    </div>
  </div>
</template>

<script>
import ViewDecoratorItem from '@baserow/modules/database/components/view/ViewDecoratorItem.vue'

export default {
  name: 'ViewDecoratorList',
  components: { ViewDecoratorItem },
  props: {
    view: {
      type: Object,
      required: true,
    },
  },
  computed: {
    viewDecoratorTypes() {
      return this.$registry
        .getOrderedList('viewDecorator')
        .filter((deco) => deco.isCompatible(this.view))
    },
  },
  methods: {
    isDisabled(decoratorType) {
      return (
        decoratorType.isDeactivated({
          view: this.view,
        }) || !decoratorType.canAdd({ view: this.view })[0]
      )
    },
    getTooltip(decoratorType) {
      if (
        decoratorType.isDeactivated({
          view: this.view,
        })
      ) {
        return decoratorType.getDeactivatedText()
      }
      const [canAdd, disabledReason] = decoratorType.canAdd({ view: this.view })
      if (!canAdd) {
        return disabledReason
      }
      return ''
    },
    addDecoration(decoratorType) {
      if (this.isDisabled(decoratorType)) {
        return
      }
      this.$emit('select', decoratorType)
    },
  },
}
</script>
