import RuntimeFormulaContext from '@baserow/modules/core/runtimeFormulaContext'
import { resolveFormula } from '@baserow/formula'

export default {
  props: {
    element: {
      type: Object,
      required: true,
    },
    page: {
      type: Object,
      required: true,
    },
    builder: {
      type: Object,
      required: true,
    },
    mode: {
      // editing = being editing by the page editor
      // preview = previewing the application
      // public = publicly published application
      type: String,
      required: false,
      default: '',
    },
  },
  computed: {
    isEditable() {
      return this.mode === 'editing'
    },
    runtimeFormulaContext() {
      /**
       * This proxy allow the RuntimeFormulaContextClass to act like a regular object.
       */
      return new Proxy(
        new RuntimeFormulaContext(
          this.$registry.getAll('builderDataProvider'),
          {
            builder: this.builder,
            page: this.page,
            mode: this.mode,
          }
        ),
        {
          get(target, prop) {
            return target.get(prop)
          },
        }
      )
    },
    formulaFunctions() {
      return {
        get: (name) => {
          return this.$registry.get('runtimeFormulaFunction', name)
        },
      }
    },
  },
  methods: {
    resolveFormula(formula) {
      return resolveFormula(
        formula,
        this.formulaFunctions,
        this.runtimeFormulaContext
      )
    },
  },
}
