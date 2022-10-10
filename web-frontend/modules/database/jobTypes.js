import { JobType } from '@baserow/modules/core/jobTypes'

import SidebarItemPendingJob from '@baserow/modules/database/components/sidebar/SidebarItemPendingJob.vue'

export class DuplicateTableJobType extends JobType {
  static getType() {
    return 'duplicate_table'
  }

  getName() {
    return 'duplicateTable'
  }

  getSidebarText(job) {
    const { i18n } = this.app
    return i18n.t('duplicateTableJobType.duplicating') + '...'
  }

  getSidebarComponent() {
    return SidebarItemPendingJob
  }

  isJobPartOfApplication(job, application) {
    return job.original_table.database_id === application.id
  }

  async onJobFailed(job) {
    const { i18n, store } = this.app

    store.dispatch(
      'notification/error',
      {
        title: i18n.t('clientHandler.notCompletedTitle'),
        message: i18n.t('clientHandler.notCompletedDescription'),
      },
      { root: true }
    )
    await store.dispatch('job/forceDelete', job)
  }

  async onJobDone(job) {
    const { i18n, store } = this.app

    const duplicatedTable = job.duplicated_table
    const database = store.getters['application/get'](
      duplicatedTable.database_id
    )

    await store.dispatch('table/forceUpsert', {
      database,
      data: duplicatedTable,
    })

    store.dispatch('notification/info', {
      title: i18n.t('duplicateTableJobType.duplicatedTitle'),
      message: duplicatedTable.name,
    })

    store.dispatch('job/forceDelete', job)
  }
}
