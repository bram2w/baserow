import RuntimeFormulaContext from '@baserow/modules/core/runtimeFormulaContext'
import { resolveFormula } from '@baserow/modules/core/formula'
import { ClickEvent, SubmitEvent } from '@baserow/modules/builder/eventTypes'

export default {
  inject: ['builder', 'page', 'mode'],
  props: {
    element: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      workflowActionsInProgress: false,
    }
  },
  computed: {
    elementType() {
      return this.$registry.get('element', this.element.type)
    },
    isEditable() {
      return this.mode === 'editing'
    },
    applicationContext() {
      return {
        builder: this.builder,
        page: this.page,
        mode: this.mode,
        element: this.element,
      }
    },
    runtimeFormulaContext() {
      /**
       * This proxy allow the RuntimeFormulaContextClass to act like a regular object.
       */
      return new Proxy(
        new RuntimeFormulaContext(
          this.$registry.getAll('builderDataProvider'),
          this.applicationContext
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
      try {
        return resolveFormula(
          formula,
          this.formulaFunctions,
          this.runtimeFormulaContext
        )
      } catch (e) {
        return ''
      }
    },
    async fireEvent(EventType) {
      if (this.mode !== 'editing') {
        this.workflowActionsInProgress = true

        const workflowActions = this.$store.getters[
          'workflowAction/getElementWorkflowActions'
        ](this.page, this.element.id)

        await new EventType({
          i18n: this.$i18n,
          store: this.$store,
          registry: this.$registry,
        }).fire({
          workflowActions,
          resolveFormula: this.resolveFormula,
          applicationContext: this.applicationContext,
        })

        this.workflowActionsInProgress = false
      }
    },
    fireClickEvent() {
      return this.fireEvent(ClickEvent)
    },
    fireSubmitEvent() {
      this.fireEvent(SubmitEvent)
    },
  },
}
