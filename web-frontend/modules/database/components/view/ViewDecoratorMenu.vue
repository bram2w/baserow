<template>
  <div>
    <a
      ref="contextLink"
      class="header__filter-link"
      :class="{ 'active--primary': decoratorCount > 0 }"
      @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 4)"
    >
      <i class="header__filter-icon fas fa-palette"></i>
      <span class="header__filter-name">
        {{
          $tc('viewDecorator.decorator', decoratorCount, {
            count: decoratorCount,
          })
        }}
      </span>
    </a>
    <ViewDecoratorContext
      ref="context"
      :view="view"
      :table="table"
      :fields="fields"
      :primary="primary"
      :read-only="readOnly"
      @changed="$emit('changed')"
    ></ViewDecoratorContext>
  </div>
</template>

<script>
import ViewDecoratorContext from '@baserow/modules/database/components/view/ViewDecoratorContext'

export default {
  name: 'ViewDecoratorMenu',
  components: { ViewDecoratorContext },
  props: {
    primary: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    decoratorCount() {
      return this.view.decorations.filter(({ type }) => {
        return !this.$registry
          .get('viewDecorator', type)
          .isDeactivated({ view: this.view })
      }).length
    },
  },
}
</script>
