export default (client, $hasFeature) => {
  return {
    // TODO implement once endpoint exists
    get(group) {
      if ($hasFeature('RBAC', group.id)) {
        return {
          data: [
            { uid: 'ADMIN', isBillable: true },
            { uid: 'BUILDER', isBillable: true },
            { uid: 'EDITOR', isBillable: true },
            { uid: 'COMMENTER', isBillable: false },
            { uid: 'VIEWER', isBillable: false },
            { uid: 'NO_ACCESS', isBillable: false },
            {
              uid: 'NO_ROLE_LOW_PRIORITY',
              allowed_scope_types: ['group'],
              allowed_subject_types: ['auth.User'],
              isBillable: false,
            },
          ],
        }
      }
      return {
        data: [
          { uid: 'ADMIN', isBillable: false },
          { uid: 'MEMBER', isBillable: false },
        ],
      }
    },
  }
}
