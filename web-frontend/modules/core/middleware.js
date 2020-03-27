import authentication from '@baserow/modules/core/middleware/authentication'
import authenticated from '@baserow/modules/core/middleware/authenticated'
import groupsAndApplications from '@baserow/modules/core/middleware/groupsAndApplications'

/* eslint-disable-next-line */
import Middleware from './middleware'

Middleware.authentication = authentication
Middleware.authenticated = authenticated
Middleware.groupsAndApplications = groupsAndApplications
