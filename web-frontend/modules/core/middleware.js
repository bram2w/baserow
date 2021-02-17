import settings from '@baserow/modules/core/middleware/settings'
import authentication from '@baserow/modules/core/middleware/authentication'
import authenticated from '@baserow/modules/core/middleware/authenticated'
import staff from '@baserow/modules/core/middleware/staff'
import groupsAndApplications from '@baserow/modules/core/middleware/groupsAndApplications'

/* eslint-disable-next-line */
import Middleware from './middleware'

Middleware.settings = settings
Middleware.authentication = authentication
Middleware.authenticated = authenticated
Middleware.staff = staff
Middleware.groupsAndApplications = groupsAndApplications
