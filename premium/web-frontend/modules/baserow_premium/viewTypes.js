import {
  maxPossibleOrderValue,
  ViewType,
} from '@baserow/modules/database/viewTypes'
import { SingleSelectFieldType } from '@baserow/modules/database/fieldTypes'
import KanbanView from '@baserow_premium/components/views/kanban/KanbanView'
import KanbanViewHeader from '@baserow_premium/components/views/kanban/KanbanViewHeader'
import { PremiumPlugin } from '@baserow_premium/plugins'

class PremiumViewType extends ViewType {
  getDeactivatedText() {
    return this.app.i18n.t('premium.deactivated')
  }

  isDeactivated() {
    return !PremiumPlugin.hasValidPremiumLicense(
      this.app.store.getters['auth/getAdditionalUserData']
    )
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
    return 'Kanban'
  }

  canFilter() {
    return false
  }

  canSort() {
    return false
  }

  getHeaderComponent() {
    return KanbanViewHeader
  }

  getComponent() {
    return KanbanView
  }

  async fetch({ store }, view, fields, primary, storePrefix = '') {
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
    primary,
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
    primary,
    values,
    metadata,
    storePrefix = ''
  ) {
    if (this.isCurrentView(store, tableId)) {
      await store.dispatch(storePrefix + 'view/kanban/createdNewRow', {
        fields,
        primary,
        values,
      })
    }
  }

  async rowUpdated(
    { store },
    tableId,
    fields,
    primary,
    row,
    values,
    metadata,
    storePrefix = ''
  ) {
    if (this.isCurrentView(store, tableId)) {
      await store.dispatch(storePrefix + 'view/kanban/updatedExistingRow', {
        fields,
        primary,
        row,
        values,
      })
    }
  }

  async rowDeleted({ store }, tableId, fields, primary, row, storePrefix = '') {
    if (this.isCurrentView(store, tableId)) {
      await store.dispatch(storePrefix + 'view/kanban/deletedExistingRow', {
        row,
      })
    }
  }

  async fieldCreated({ dispatch }, table, field, fieldType, storePrefix = '') {
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

  _setSingleSelectFieldToNull({ rootGetters, dispatch }, field) {
    rootGetters['view/getAll']
      .filter((view) => view.type === this.type)
      .forEach((view) => {
        if (view.single_select_field === field.id) {
          dispatch(
            'view/forceUpdate',
            {
              view,
              values: { single_select_field: null },
            },
            { root: true }
          )
        }
      })
  }

  fieldUpdated(context, field, oldField, fieldType, storePrefix) {
    // If the field type has changed from a single select field to something else,
    // it could be that there are kanban views that depending on that field. So we
    // need to change to type to null if that's the case.
    const type = SingleSelectFieldType.getType()
    if (oldField.type === type && field.type !== type) {
      this._setSingleSelectFieldToNull(context, field)
    }
  }

  fieldDeleted(context, field, fieldType, storePrefix = '') {
    // We want to loop over all kanban views that we have in the store and check if
    // they were depending on this deleted field. If that's case, we can set it to null
    // because it doesn't exist anymore.
    this._setSingleSelectFieldToNull(context, field)
  }
}
