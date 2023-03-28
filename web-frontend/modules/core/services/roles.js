export default (client, $hasFeature) => {
  return {
    // TODO implement once endpoint exists
    get(workspace) {
      if ($hasFeature('RBAC', workspace.id)) {
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
              allowed_scope_types: ['workspace'],
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
