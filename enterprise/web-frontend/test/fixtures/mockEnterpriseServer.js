import { aUser } from './user'

export default class MockEnterpriseServer {
  constructor(mock) {
    this.mock = mock
  }

  aUser(options) {
    aUser(options)
  }
}
