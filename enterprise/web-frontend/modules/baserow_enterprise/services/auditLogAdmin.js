import baseService from '@baserow/modules/core/crudTable/baseService'
import jobService from '@baserow/modules/core/services/job'

export default (client) => {
  return Object.assign(baseService(client, '/admin/audit-log/'), {
    fetchUsers(page, search) {
      const usersUrl = '/admin/audit-log/users/'
      const userPaginatedService = baseService(client, usersUrl)
      return userPaginatedService.fetch(usersUrl, page, search, [], [])
    },
    fetchGroups(page, search) {
      const groupsUrl = '/admin/audit-log/groups/'
      const groupPaginatedService = baseService(client, groupsUrl)
      return groupPaginatedService.fetch(groupsUrl, page, search, [], [])
    },
    fetchActionTypes(page, search) {
      const actionTypesUrl = '/admin/audit-log/action-types/'
      const actionTypePaginatedService = baseService(client, actionTypesUrl)
      return actionTypePaginatedService.fetch(
        actionTypesUrl,
        page,
        search,
        [],
        []
      )
    },
    startExportCsvJob(data) {
      return client.post('/admin/audit-log/export/', data)
    },
    getExportJobInfo(jobId) {
      return jobService(client).get(jobId)
    },
    async getLastExportJobs(maxCount = 3) {
      const { data } = await jobService(client).fetchAll({
        states: ['!failed'],
      })
      const jobs = data.jobs || []
      return jobs
        .filter((job) => job.type === 'audit_log_export')
        .slice(0, maxCount)
    },
  })
}
