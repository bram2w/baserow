import settings from '@baserow/modules/core/middleware/settings'
import authentication from '@baserow/modules/core/middleware/authentication'
import authenticated from '@baserow/modules/core/middleware/authenticated'
import staff from '@baserow/modules/core/middleware/staff'
import admin from '@baserow/modules/core/middleware/admin'
import groupsAndApplications from '@baserow/modules/core/middleware/groupsAndApplications'
import pendingJobs from '@baserow/modules/core/middleware/pendingJobs'
import urlCheck from '@baserow/modules/core/middleware/urlCheck'

/* eslint-disable-next-line */
import Middleware from './middleware'

Middleware.settings = settings
Middleware.authentication = authentication
Middleware.authenticated = authenticated
Middleware.staff = staff
Middleware.admin = admin
Middleware.groupsAndApplications = groupsAndApplications
Middleware.pendingJobs = pendingJobs
Middleware.urlCheck = urlCheck
