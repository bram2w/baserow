import { DatabaseApplication } from '@/modules/database/application'

export default ({ store }) => {
  store.dispatch('application/register', new DatabaseApplication())
}
