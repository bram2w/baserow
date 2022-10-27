import {
  maxPossibleOrderValue,
  ViewType,
} from '@baserow/modules/database/viewTypes'
import { SingleSelectFieldType } from '@baserow/modules/database/fieldTypes'
import KanbanView from '@baserow_premium/components/views/kanban/KanbanView'
import KanbanViewHeader from '@baserow_premium/components/views/kanban/KanbanViewHeader'
import PremiumModal from '@baserow_premium/components/PremiumModal'
import PremiumFeatures from '@baserow_premium/features'

class PremiumViewType extends ViewType {
  getDeactivatedText() {
    return this.app.i18n.t('premium.deactivated')
  }

  getDeactivatedClickModal() {
    return PremiumModal
  }

  isDeactivated(groupId) {
    return !this.app.$hasFeature(PremiumFeatures.PREMIUM, groupId)
  }
}

export class KanbanViewType extends PremiumViewType {
  static getType() {
    return 'kanban'
  }

  getIconClass() {
    return 'trello fab'
  }

  getColorClass() {
    return 'color-success'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('premium.viewType.kanban')
  }

  canFilter() {
    return true
  }

  canSort() {
    return false
  }

  canShare() {
    return true
  }

  getPublicRoute() {
    return 'database-public-kanban-view'
  }

  getHeaderComponent() {
    return KanbanViewHeader
  }

  getComponent() {
    return KanbanView
  }

  async fetch({ store }, view, fields, storePrefix = '') {
    // If the single select field is `null` we can't fetch the initial data anyway,
    // we don't have to do anything. The KanbanView component will handle it by
    // showing a form to choose or create a single select field.
    if (view.single_select_field === null) {
      await store.dispatch(storePrefix + 'view/kanban/reset')
    } else {
      await store.dispatch(storePrefix + 'view/kanban/fetchInitial', {
        kanbanId: view.id,
        singleSelectFieldId: view.single_select_field,
      })
    }
  }

  async refresh(
    { store },
    view,
    fields,
    storePrefix = '',
    includeFieldOptions = false
  ) {
    try {
      await store.dispatch(storePrefix + 'view/kanban/fetchInitial', {
        kanbanId: view.id,
        singleSelectFieldId: view.single_select_field,
        includeFieldOptions,
      })
    } catch (error) {
      if (
        error.handler.code === 'ERROR_KANBAN_VIEW_HAS_NO_SINGLE_SELECT_FIELD'
      ) {
        store.dispatch(storePrefix + 'view/kanban/reset')
      } else {
        throw error
      }
    }
  }

  async fieldOptionsUpdated({ store }, view, fieldOptions, storePrefix) {
    await store.dispatch(
      storePrefix + 'view/kanban/forceUpdateAllFieldOptions',
      fieldOptions,
      {
        root: true,
      }
    )
  }

  updated(context, view, oldView, storePrefix) {
    // If the single select field has changed, we want to trigger a refresh of the
    // page by returning true.
    return view.single_select_field !== oldView.single_select_field
  }

  async rowCreated(
    { store },
    tableId,
    fields,
    values,
    metadata,
    storePrefix = ''
  ) {
    if (this.isCurrentView(store, tableId)) {
      await store.dispatch(storePrefix + 'view/kanban/createdNewRow', {
        view: store.getters['view/getSelected'],
        values,
        fields,
      })
    }
  }

  async rowUpdated(
    { store },
    tableId,
    fields,
    row,
    values,
    metadata,
    storePrefix = ''
  ) {
    if (this.isCurrentView(store, tableId)) {
      await store.dispatch(storePrefix + 'view/kanban/updatedExistingRow', {
        view: store.getters['view/getSelected'],
        fields,
        row,
        values,
      })
    }
  }

  async rowDeleted({ store }, tableId, fields, row, storePrefix = '') {
    if (this.isCurrentView(store, tableId)) {
      await store.dispatch(storePrefix + 'view/kanban/deletedExistingRow', {
        view: store.getters['view/getSelected'],
        row,
        fields,
      })
    }
  }

  async afterFieldCreated(
    { dispatch },
    table,
    field,
    fieldType,
    storePrefix = ''
  ) {
    const value = fieldType.getEmptyValue(field)
    await dispatch(
      storePrefix + 'view/kanban/addField',
      { field, value },
      { root: true }
    )
    await dispatch(
      storePrefix + 'view/kanban/setFieldOptionsOfField',
      {
        field,
        // The default values should be the same as in the `KanbanViewFieldOptions`
        // model in the backend to stay consistent.
        values: {
          hidden: true,
          order: maxPossibleOrderValue,
        },
      },
      { root: true }
    )
  }

  afterFieldUpdated(context, field, oldField, fieldType, storePrefix) {
    // Make sure that all Kanban views don't depend on fields that
    // have been converted to another type
    const type = SingleSelectFieldType.getType()
    if (oldField.type === type && field.type !== type) {
      this._setFieldToNull(context, field, 'single_select_field')
      this._setFieldToNull(context, field, 'card_cover_image_field')
    }
  }

  afterFieldDeleted(context, field, fieldType, storePrefix = '') {
    // Make sure that all Kanban views don't depend on fields that
    // have been deleted
    this._setFieldToNull(context, field, 'single_select_field')
    this._setFieldToNull(context, field, 'card_cover_image_field')
  }
}
