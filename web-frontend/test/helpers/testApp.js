import setupCore from '@baserow/modules/core/plugin'
import axios from 'axios'
import setupDatabasePlugin from '@baserow/modules/database/plugin'
import { bootstrapVueContext } from '@baserow/test/helpers/components'
import MockAdapter from 'axios-mock-adapter'
import _ from 'lodash'
import { MockServer } from '@baserow/test/fixtures/mockServer'
import flushPromises from 'flush-promises'

/**
 * Uses the real baserow plugins to setup a Vuex store and baserow registry
 * correctly.
 */
function _createBaserowStoreAndRegistry(app, vueContext) {
  const store = new vueContext.vuex.Store({})
  setupCore({ store, app }, (name, dep) => {
    app[`$${name}`] = dep
  })
  store.$registry = app.$registry
  store.$client = axios
  store.app = app
  app.$store = store
  setupDatabasePlugin({
    store,
    app,
  })
  return store
}

/**
 * An acceptance testing framework for testing Baserow components and surrounding logic
 * like stores.
 * TestApp sets up baserow components, registries and stores so they work out of the
 * box and can be tested without having to:
 *  - wait 30+ seconds for a Nuxt server to startup and build
 *  - mock out stores, registries or carve arbitrary boundaries in
 *    the tests causing problems when store and component logic is tightly
 *    coupled.
 *
 * To use create an instance of this class in your beforeAll
 * test suite hook and make sure to call testApp.afterEach() in the afterEach hook.
 *
 * The following attributes are exposed for use in your tests:
 * testApp.mockServer : a helper class providing methods to initialize a fake
 *                      baserow server with consistent test data.
 * testApp.mock       : a mock axios adapter used to mock out HTTP calls to the server,
 *                      also used by testApp.mockServer to actually do the server call
 *                      mocking.
 * testApp.store      : a Vuex store populated with Baserow's stores ready for you to
 *                      commit, get and dispatch to.
 * UIHelpers          : a collection of methods which know how to perform common actions
 *                      on Baserow's components.
 *
 */
export class TestApp {
  constructor() {
    // In the future we can extend this stub realtime implementation to perform
    // useful testing of realtime interaction in the frontend!
    this._realtime = {
      registerEvent(e, f) {},
      subscribe(e, f) {},
    }
    // Various stub and mock attributes which will be injected into components
    // mounted using TestApp.
    this._app = {
      $realtime: this._realtime,
      $cookies: {
        set(name, id, value) {},
      },
      $env: {
        PUBLIC_WEB_FRONTEND_URL: 'https://localhost/',
      },
    }
    this.mock = new MockAdapter(axios)
    this._vueContext = bootstrapVueContext()
    this.store = _createBaserowStoreAndRegistry(this._app, this._vueContext)
    this._initialCleanStoreState = _.cloneDeep(this.store.state)
    this.mockServer = new MockServer(this.mock, this.store)
  }

  /**
   * Cleans up after a test run performed by TestApp. Make sure you call this
   * in your test suits afterEach method!
   */
  async afterEach() {
    this.mock.reset()
    this.store.replaceState(_.cloneDeep(this._initialCleanStoreState))
    this._vueContext.teardownVueContext()
    await flushPromises()
  }

  /**
   * Creates a fully rendered version of the provided Component and calls
   * asyncData on the component at the correct time with the provided params.
   */
  async mount(Component, { asyncDataParams = {} }) {
    if (Object.prototype.hasOwnProperty.call(Component, 'asyncData')) {
      const data = await Component.asyncData({
        store: this.store,
        params: asyncDataParams,
        error: fail,
        app: this._app,
      })
      Component.data = function () {
        return data
      }
    }
    return this._vueContext.vueTestUtils.mount(Component, {
      localVue: this._vueContext.vue,
      mocks: this._app,
    })
  }
}
/**
 * Various helper functions which interact with baserow components. Lean towards
 * putting and sharing any test code which relies on specific details of how baserow
 * components are structured and styled in here This way there is a single place
 * to fix when changes are made to the components instead of 30 different test cases.
 */
export const UIHelpers = {
  async performSearch(tableComponent, searchTerm) {
    const searchBox = tableComponent.get(
      'input[placeholder*="Search in all rows"]'
    )
    await searchBox.setValue(searchTerm)
    await searchBox.trigger('submit')
    await flushPromises()
  },
  async startEditForCellContaining(tableComponent, htmlInsideCellToSearchFor) {
    const targetCell = tableComponent
      .findAll('.grid-view__cell')
      .filter((w) => w.html().includes(htmlInsideCellToSearchFor))
      .at(0)

    await targetCell.trigger('click')

    const activeCell = tableComponent.get('.grid-view__cell.active')
    // Double click to start editing cell
    await activeCell.trigger('click')
    await activeCell.trigger('click')

    return activeCell.find('input')
  },
}
