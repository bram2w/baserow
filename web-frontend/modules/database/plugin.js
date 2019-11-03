import { DatabaseApplication } from '@/modules/database/application'
import tableStore from '@/modules/database/store/table'

export default ({ store }) => {
  store.registerModule('table', tableStore)
  store.dispatch('application/register', new DatabaseApplication())
}
