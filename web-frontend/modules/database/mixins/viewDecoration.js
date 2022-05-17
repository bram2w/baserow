/**
 * A mixin that can be used in combination with the view filter input components. If
 * contains the expected props and it has a computed property that finds the field
 * object related to filter field id.
 */
export default {
  props: {
    view: {
      type: Object,
      required: false,
      default: undefined,
    },
    fields: {
      type: Array,
      required: true,
    },
    primary: {
      type: Object,
      required: true,
    },
  },
  computed: {
    allTableFields() {
      return [this.primary, ...this.fields]
    },
    activeDecorations() {
      return this.view.decorations
        .map((decoration) => {
          const deco = { decoration }

          deco.decoratorType = this.$registry.get(
            'viewDecorator',
            decoration.type
          )

          deco.component = deco.decoratorType.getComponent()
          deco.place = deco.decoratorType.getPlace()

          if (decoration.value_provider_type) {
            deco.valueProviderType = this.$registry.get(
              'decoratorValueProvider',
              decoration.value_provider_type
            )

            deco.propsFn = (row) => {
              return {
                value: deco.valueProviderType.getValue({
                  row,
                  fields: this.allTableFields,
                  options: decoration.value_provider_conf,
                }),
              }
            }
          }

          return deco
        })
        .filter(
          ({ decoratorType }) =>
            !decoratorType.isDeactivated({ view: this.view })
        )
    },
    decorationsByPlace() {
      return this.activeDecorations
        .filter(({ valueProviderType }) => valueProviderType)
        .reduce((prev, deco) => {
          if (deco.valueProviderType) {
            const decType = deco.decoratorType.getPlace()
            prev[decType] = [...(prev[decType] || []), deco]
          }
          return prev
        }, {})
    },
  },
}
