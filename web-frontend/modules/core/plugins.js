import { Registerable } from '@baserow/modules/core/registry'

/**
 * The name plugin might be a bit confusing because you also have Nuxt plugins, but
 * this is not the same. A plugin can contain hooks for certain events such as when
 * a user account is created.
 */
export class BaserowPlugin extends Registerable {
  constructor(...args) {
    super(...args)
    this.type = this.getType()
  }

  /**
   * Hook that is called when a user creates a new account. This can for example be
   * used for submitting an analytical event.
   */
  userCreated(user, context) {}

  /**
   * Every registered plugin can have a component that's rendered at the top of the
   * left sidebar.
   */
  getSidebarTopComponent() {
    return null
  }

  /*
   * Every registered plugin can display an item in the main sidebar menu.
   */
  getSidebarMainMenuComponent() {
    return null
  }

  /**
   * Every registered plugin can display an additional item in the sidebar within
   * the workspace context.
   */
  getSidebarWorkspaceComponents(workspace) {
    return null
  }

  /*
   * Every registered plugin can display a component in the links section of the
   * dashboard sidebar.
   */
  getDashboardSidebarLinksComponent() {
    return null
  }

  /*
   * Every registered plugin can display a component in the `DashboardWorkspace`
   * component directly after the workspace name.
   */
  getDashboardWorkspaceExtraComponent() {
    return null
  }

  /*
   * Every registered plugin can display a component in the `DashboardWorkspace`
   * component directly below the workspace name.
   */
  getDashboardWorkspaceComponent() {
    return null
  }

  /**
   * Because the dashboard could contain dynamic `getDashboardWorkspaceComponent` and
   * `getDashboardWorkspaceExtraComponent` components, it could be that additional data
   * must be fetched from the backend when the page first loads. This method can be
   * overwritten to do that.
   *
   * Optinally, a workspace id can be provided to fetch only data for a particular
   * workspace.
   */
  fetchAsyncDashboardData(context, data, workspaceId) {
    return data
  }

  /**
   * Tells core Baserow how new fetched data for a particular workspace
   * should be merged with previously fetched dashboard data from
   * fetchAsyncDashboardData()
   */
  mergeDashboardData(data, newData) {
    return data
  }

  /**
   * Every registered plugin can display a component in the `AuthRegister` component
   * directly at the bottom of the form. This component can be used to extend the
   * register functionality.
   */
  getRegisterComponent() {
    return null
  }

  /**
   * Every registered plugin can display a component in the `app.vue` layout. This
   * is the root component that's being used for every authenticated page in the app.
   */
  getAppLayoutComponent() {
    return null
  }

  /**
   * If set, this components in the list will be rendered directly after the user
   * creates an account. It must emit a `success` event when the user must be
   * redirected to the next page.
   */
  getAfterSignupStepComponent() {
    return []
  }

  /*
   * Every registered plugin can display multiple additional public share link options
   * which will be visible on the share public view context.
   */
  getAdditionalShareLinkOptions() {
    return []
  }

  /**
   * Every registered plugin can display multiple additional context items in the
   * database context displayed by the sidebar when opening the context menu of a
   * database.
   * @returns {*[]}
   */
  getAdditionalDatabaseContextComponents(workspace, database) {
    return []
  }

  /**
   * Every registered plugin can display multiple additional context items in the
   * table context displayed by the sidebar when opening the context menu of a
   * table.
   * @returns {*[]}
   */
  getAdditionalTableContextComponents(workspace, table) {
    return []
  }

  /**
   * If set, `getExtraSnapshotModalComponents` will allow plugins to decide what kind of
   * copy is shown in the snapshots modal's Alert box.
   */
  getExtraSnapshotModalComponents(workspace) {
    return null
  }

  /**
   * Some features are optionally enabled, this function will be called when the
   * $hasFeature directive is called on each plugin to check if any of the plugins
   * enable the particular feature.
   * @returns {boolean}
   */
  hasFeature(feature, forSpecificWorkspace) {
    return false
  }
}
