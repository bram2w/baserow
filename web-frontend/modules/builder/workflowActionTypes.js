import { WorkflowActionType } from '@baserow/modules/core/workflowActionTypes'
import NotificationWorkflowActionForm from '@baserow/modules/builder/components/workflowAction/NotificationWorkflowActionForm.vue'
import OpenPageWorkflowActionForm from '@baserow/modules/builder/components/workflowAction/OpenPageWorkflowActionForm'
import CreateRowWorkflowActionForm from '@baserow/modules/builder/components/workflowAction/CreateRowWorkflowAction.vue'
import UpdateRowWorkflowActionForm from '@baserow/modules/builder/components/workflowAction/UpdateRowWorkflowAction.vue'
import { DataProviderType } from '@baserow/modules/core/dataProviderTypes'
import { ensureString } from '@baserow/modules/core/utils/validator'

export class NotificationWorkflowActionType extends WorkflowActionType {
  static getType() {
    return 'notification'
  }

  get form() {
    return NotificationWorkflowActionForm
  }

  get label() {
    return this.app.i18n.t('workflowActionTypes.notificationLabel')
  }

  execute({ workflowAction: { title, description }, resolveFormula }) {
    return this.app.store.dispatch('toast/info', {
      title: ensureString(resolveFormula(title)),
      message: ensureString(resolveFormula(description)),
    })
  }

  getDataSchema(applicationContext, workflowAction) {
    return null
  }
}

export class OpenPageWorkflowActionType extends WorkflowActionType {
  static getType() {
    return 'open_page'
  }

  get form() {
    return OpenPageWorkflowActionForm
  }

  get label() {
    return this.app.i18n.t('workflowActionTypes.openPageLabel')
  }

  execute({
    workflowAction: { url },
    applicationContext: { builder, mode },
    resolveFormula,
  }) {
    let urlParsed = ensureString(resolveFormula(url))

    if (urlParsed.startsWith('/')) {
      if (mode === 'preview') {
        urlParsed = `/builder/${builder.id}/preview${urlParsed}`
      }
      return this.app.router.push(urlParsed)
    }

    if (!urlParsed.startsWith('http')) {
      urlParsed = `https://${urlParsed}`
    }

    window.location.replace(urlParsed)
  }

  getDataSchema(applicationContext, workflowAction) {
    return null
  }
}

export class LogoutWorkflowActionType extends WorkflowActionType {
  static getType() {
    return 'logout'
  }

  get form() {
    return null
  }

  get label() {
    return this.app.i18n.t('workflowActionTypes.logoutLabel')
  }

  execute() {
    return this.app.store.dispatch('userSourceUser/logoff')
  }
}

export class WorkflowActionServiceType extends WorkflowActionType {
  execute({ workflowAction: { id }, applicationContext, resolveFormula }) {
    return this.app.store.dispatch('workflowAction/dispatchAction', {
      workflowActionId: id,
      data: DataProviderType.getAllActionDispatchContext(
        this.app.$registry.getAll('builderDataProvider'),
        applicationContext
      ),
    })
  }

  getDataSchema(workflowAction) {
    if (!workflowAction?.service?.schema) {
      return null
    }
    return {
      title: this.label,
      type: 'object',
      properties: workflowAction?.service?.schema?.properties,
    }
  }
}

export class CreateRowWorkflowActionType extends WorkflowActionServiceType {
  static getType() {
    return 'create_row'
  }

  get form() {
    return CreateRowWorkflowActionForm
  }

  get label() {
    return this.app.i18n.t('workflowActionTypes.createRowLabel')
  }
}

export class UpdateRowWorkflowActionType extends WorkflowActionServiceType {
  static getType() {
    return 'update_row'
  }

  get form() {
    return UpdateRowWorkflowActionForm
  }

  get label() {
    return this.app.i18n.t('workflowActionTypes.updateRowLabel')
  }
}
