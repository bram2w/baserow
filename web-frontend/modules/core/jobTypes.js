import { notifyIf } from '@baserow/modules/core/utils/error'
import { Registerable } from '@baserow/modules/core/registry'
import SidebarApplicationPendingJob from '@baserow/modules/core/components/sidebar/SidebarApplicationPendingJob'

/**
 * The job type base class that can be extended when creating a plugin
 * for the frontend.
 */
export class JobType extends Registerable {
  /**
   * The font awesome 5 icon name that is used as convenience for the user to
   * recognize certain job types. If you for example want the database
   * icon, you must return 'database' here. This will result in the classname
   * 'fas fa-database'.
   */
  getIconClass() {
    return null
  }

  /**
   * A human readable name of the job type.
   */
  getName() {
    return null
  }

  /**
   * Returns the text to show in the sidebar when the job is running.
   */
  getSidebarText(job) {
    return ''
  }

  /**
   * The sidebar component will be rendered in the sidebar if the application is
   * in the selected group. All the applications of a group are listed in the
   * sidebar and this component should give the user the possibility to select
   * that application.
   */
  getSidebarComponent() {
    return null
  }

  constructor(...args) {
    super(...args)
    this.type = this.getType()

    if (this.type === null) {
      throw new Error('The type name of an application type must be set.')
    }
    if (this.name === null) {
      throw new Error('The name of an application type must be set.')
    }
  }

  /**
   * Every time a fresh job object is fetched from the backend, it will
   * be populated, this is the moment to update some values. Because each
   * jobType can have unique properties, they might need to be populated.
   * This method can be overwritten in order the populate the correct values.
   */
  populate(job) {
    return job
  }

  /**
   * Returns true if the specific job is part of the group
   */
  isJobPartOfGroup(job, group) {
    return false
  }

  /**
   * Returns true if the specific job is part of the application
   */
  isJobPartOfApplication(job, application) {
    return false
  }

  /**
   * When an application is deleted it could be that an action should be taken,
   * like redirect the user to another page. This method is called when application
   * of this type is deleted.
   */
  beforeDelete(job) {}

  /**
   * Before the application values are updated, they can be modified here. This
   * might be needed because providing certain values could break the update.
   */
  async beforeUpdate(job, data) {}

  async afterUpdate(job, data) {
    if (job.state === 'finished') {
      await this.onJobDone(job, data)
    } else if (job.state === 'failed') {
      await this.onJobFailed(job, data)
    }
  }

  async onJobDone(job) {}
  async onJobFailed(job) {}
}

export class DuplicateApplicationJobType extends JobType {
  static getType() {
    return 'duplicate_application'
  }

  getIconClass() {
    // TODO: This should be moved to a registry and in the database module.
    return 'database'
  }

  getName() {
    return 'duplicateApplication'
  }

  getSidebarText(job) {
    const { i18n } = this.app
    return i18n.t('duplicateApplicationJobType.duplicating') + '... '
  }

  getSidebarComponent() {
    return SidebarApplicationPendingJob
  }

  isJobPartOfGroup(job, group) {
    return job.original_application.group.id === group.id
  }

  async onJobDone(job) {
    const { i18n, store } = this.app
    const application = job.duplicated_application
    try {
      await store.dispatch('application/forceCreate', application)
      store.dispatch('notification/info', {
        title: i18n.t('duplicateApplicationJobType.duplicatedTitle'),
        message: application.name,
      })
    } catch (error) {
      notifyIf(error, 'application')
    } finally {
      await store.dispatch('job/forceDelete', job)
    }
  }

  async onJobFailed(job) {
    const { i18n, store } = this.app
    await store.dispatch(
      'notification/error',
      {
        title: i18n.t('clientHandler.notCompletedTitle'),
        message: i18n.t('clientHandler.notCompletedDescription'),
      },
      { root: true }
    )
    await this.app.store.dispatch('job/forceDelete', job)
  }
}

export class InstallTemplateJobType extends JobType {
  static getType() {
    return 'install_template'
  }

  getIconClass() {
    // TODO: This should be moved to a registry and in the database module.
    return 'database'
  }

  getName() {
    return 'installTemplate'
  }

  getSidebarText(job) {
    const { i18n } = this.app
    return i18n.t('InstallTemplateJobType.installing') + '... '
  }

  getSidebarComponent() {
    return SidebarApplicationPendingJob
  }

  isJobPartOfGroup(job, group) {
    return job.group.id === group.id
  }

  async onJobDone(job) {
    const { i18n, store } = this.app
    // Installing a template has just created a couple of applications in the
    // group. The response contains those applications and we can add them to the
    // store so that the user can view the installed template right away.
    const installedApplications = job.installed_applications
    try {
      for (const application of installedApplications) {
        await store.dispatch('application/forceCreate', application)
      }
      store.dispatch('notification/info', {
        title: i18n.t('InstallTemplateJobType.installedTitle'),
        message: installedApplications[0].name,
      })
    } catch (error) {
      notifyIf(error, 'application')
    } finally {
      await store.dispatch('job/forceDelete', job)
    }
  }

  async onJobFailed(job) {
    const { i18n, store } = this.app
    await store.dispatch(
      'notification/error',
      {
        title: i18n.t('clientHandler.notCompletedTitle'),
        message: i18n.t('clientHandler.notCompletedDescription'),
      },
      { root: true }
    )
    await this.app.store.dispatch('job/forceDelete', job)
  }
}
