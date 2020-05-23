import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import { GridViewType } from '@baserow/modules/database/viewTypes'
import {
  TextFieldType,
  LongTextFieldType,
  NumberFieldType,
  BooleanFieldType,
} from '@baserow/modules/database/fieldTypes'

import tableStore from '@baserow/modules/database/store/table'
import viewStore from '@baserow/modules/database/store/view'
import fieldStore from '@baserow/modules/database/store/field'
import gridStore from '@baserow/modules/database/store/view/grid'

export default ({ store, app }) => {
  store.registerModule('table', tableStore)
  store.registerModule('view', viewStore)
  store.registerModule('field', fieldStore)
  store.registerModule('view/grid', gridStore)

  app.$registry.register('application', new DatabaseApplicationType())
  app.$registry.register('view', new GridViewType())
  app.$registry.register('field', new TextFieldType())
  app.$registry.register('field', new LongTextFieldType())
  app.$registry.register('field', new NumberFieldType())
  app.$registry.register('field', new BooleanFieldType())
}
