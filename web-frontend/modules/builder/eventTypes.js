import RuntimeFormulaContext from '@baserow/modules/core/runtimeFormulaContext'
import { resolveFormula } from '@baserow/modules/core/formula'

/**
 * This might look like something that belongs in a registry, but it does not.
 *
 * There is no point in making these accessible to plugin writers so there is no
 * registry required.
 */
export class Event {
  constructor({
    i18n,
    store,
    $registry,
    name,
    label,
    applicationContextAdditions = {},
  }) {
    this.i18n = i18n
    this.store = store
    this.$registry = $registry
    this.name = name
    this.label = label
    this.applicationContextAdditions = applicationContextAdditions
  }

  async fire({ workflowActions, applicationContext }) {
    const additionalContext = {}
    const { element, recordIndexPath } = applicationContext
    const elementType = this.$registry.get('element', element.type)
    const dispatchedById = elementType.uniqueElementId(element, recordIndexPath)
    for (let i = 0; i < workflowActions.length; i += 1) {
      const workflowAction = workflowActions[i]
      const workflowActionType = this.$registry.get(
        'workflowAction',
        workflowAction.type
      )
      const localResolveFormula = (formula) => {
        const formulaFunctions = {
          get: (name) => {
            return this.$registry.get('runtimeFormulaFunction', name)
          },
        }
        const runtimeFormulaContext = new Proxy(
          new RuntimeFormulaContext(
            this.$registry.getAll('builderDataProvider'),
            {
              ...applicationContext,
              ...this.applicationContextAdditions,
              previousActionResults: additionalContext,
            }
          ),
          {
            get(target, prop) {
              return target.get(prop)
            },
          }
        )
        try {
          return resolveFormula(
            formula,
            formulaFunctions,
            runtimeFormulaContext
          )
        } catch {
          return ''
        }
      }

      this.store.dispatch('workflowAction/setDispatching', {
        workflowAction,
        dispatchedById,
        isDispatching: true,
      })
      try {
        additionalContext[workflowAction.id] = await workflowActionType.execute(
          {
            workflowAction,
            additionalContext,
            applicationContext: {
              ...applicationContext,
              previousActionResults: additionalContext,
            },
            resolveFormula: localResolveFormula,
          }
        )
      } finally {
        this.store.dispatch('workflowAction/setDispatching', {
          workflowAction,
          dispatchedById: null,
          isDispatching: false,
        })
      }
    }
  }
}

export class ClickEvent extends Event {
  constructor({ namePrefix, labelSuffix, ...rest }) {
    super({
      ...rest,
      name: namePrefix ? `${namePrefix}_click` : 'click',
      label: labelSuffix
        ? `${rest.i18n.t('eventTypes.clickLabel')} ${labelSuffix}`
        : rest.i18n.t('eventTypes.clickLabel'),
    })
  }
}

export class SubmitEvent extends Event {
  constructor(args) {
    super({
      name: 'submit',
      label: args.i18n.t('eventTypes.submitLabel'),
      ...args,
    })
  }
}

export class AfterLoginEvent extends Event {
  constructor(args) {
    super({
      name: 'after_login',
      label: args.i18n.t('eventTypes.afterLoginLabel'),
      ...args,
    })
  }
}
