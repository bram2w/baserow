import { WorkflowActionType } from '@baserow/modules/core/workflowActionTypes'
import NotificationWorkflowActionForm from '@baserow/modules/builder/components/workflowAction/NotificationWorkflowActionForm.vue'
import OpenPageWorkflowActionForm from '@baserow/modules/builder/components/workflowAction/OpenPageWorkflowActionForm'

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
      title: resolveFormula(title),
      message: resolveFormula(description),
    })
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
    let urlParsed = resolveFormula(url)

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
}
