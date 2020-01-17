import { DatabaseApplicationType } from '@/modules/database/applicationTypes'
import { GridViewType } from '@/modules/database/viewTypes'
import {
  TextFieldType,
  NumberFieldType,
  BooleanFieldType
} from '@/modules/database/fieldTypes'

import tableStore from '@/modules/database/store/table'
import viewStore from '@/modules/database/store/view'
import fieldStore from '@/modules/database/store/field'

/**
 * Note that this method is actually called on the server and client side, but
 * for registering the application this is intentional. The table and view
 * types must actually be registered on both sides. Since we're adding an
 * initialized class object, which cannot be stringified we need to override the
 * object on the client side. Because both register actions don't check if the
 * type already exists, but just overrides this works for now. In the future we
 * must find a way to properly serialize the object and pass it from the server
 * to the client in order to get rid off the warning 'Cannot stringify arbitrary
 * non-POJOs DatabaseApplicationType' on the server side. There is an issue for
 * that on the backlog with id 15.
 */
export default ({ store }) => {
  store.registerModule('table', tableStore)
  store.registerModule('view', viewStore)
  store.registerModule('field', fieldStore)

  store.dispatch('application/register', new DatabaseApplicationType())
  store.dispatch('view/register', new GridViewType())
  store.dispatch('field/register', new TextFieldType())
  store.dispatch('field/register', new NumberFieldType())
  store.dispatch('field/register', new BooleanFieldType())
}
