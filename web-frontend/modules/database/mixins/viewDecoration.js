/**
 * A mixin that can be used in combination with the view filter input components. If
 * contains the expected props and it has a computed property that finds the field
 * object related to filter field id.
 */
export default {
  props: {
    database: {
      type: Object,
      required: false,
      default: undefined,
    },
    view: {
      type: Object,
      required: false,
      default: undefined,
    },
    fields: {
      type: Array,
      required: true,
    },
  },
  computed: {
    activeDecorations() {
      return this.view.decorations
        .map((decoration) => {
          const deco = { decoration }

          deco.decoratorType = this.$registry.get(
            'viewDecorator',
            decoration.type
          )

          deco.component = deco.decoratorType.getComponent(
            this.database.workspace.id
          )
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
                  fields: this.fields,
                  options: decoration.value_provider_conf,
                }),
              }
            }
          }

          return deco
        })
        .filter(
          ({ decoratorType }) =>
            !decoratorType.isDeactivated(this.database.workspace.id)
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
