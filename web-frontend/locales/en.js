export default {
  common: {
    yes: 'yes',
    no: 'no',
    wrong: 'Something went wrong',
  },
  action: {
    upload: 'Upload',
    back: 'Back',
    backToLogin: 'Back to login',
    signUp: 'Sign up',
    signIn: 'Sign in',
    createNew: 'Create new',
    create: 'Create',
    change: 'Change',
    delete: 'Delete',
    rename: 'Rename',
    add: 'Add',
    makeChoice: 'Make a choice',
    cancel: 'Cancel',
    search: 'Search',
    copy: 'Copy',
  },
  adminType: {
    settings: 'Settings',
  },
  applicationType: {
    database: 'Database',
  },
  settingType: {
    account: 'Account',
    password: 'Password',
    tokens: 'API Tokens',
  },
  userFileUploadType: {
    file: 'my device',
    url: 'a URL',
  },
  field: {
    emailAddress: 'E-mail address',
  },
  error: {
    invalidEmail: 'Please enter a valid e-mail address.',
    notMatchingPassword: 'This field must match your password field.',
    minLength: 'A minimum of {min} characters is required here.',
    maxLength: 'A maximum of {max} characters is allowed here.',
    minMaxLength:
      'A minimum of {min} and a maximum of {max} characters is allowed here.',
    requiredField: 'This field is required.',
  },
  permission: {
    admin: 'Admin',
    adminDescription: 'Can fully configure and edit groups and applications.',
    member: 'Member',
    memberDescription: 'Can fully configure and edit applications.',
  },
  fieldType: {
    singleLineText: 'Single line text',
    longText: 'Long text',
    linkToTable: 'Link to table',
    number: 'Number',
    boolean: 'Boolean',
    date: 'Date',
    lastModified: 'Last modified',
    createdOn: 'Created on',
    url: 'URL',
    email: 'Email',
    file: 'File',
    singleSelect: 'Single select',
    phoneNumber: 'Phone number',
    formula: 'Formula',
  },
  fieldErrors: {
    invalidNumber: 'Invalid number',
    maxDigits: 'Max {max} digits allowed.',
    invalidUrl: 'Invalid URL',
    max254Chars: 'Max 254 chars',
    invalidEmail: 'Invalid email',
    invalidPhoneNumber: 'Invalid Phone Number',
  },
  fieldDocs: {
    readOnly: 'This is a read only field.',
    text: 'Accepts single line text.',
    longText: 'Accepts multi line text.',
    linkRow:
      'Accepts an array containing the identifiers of the related rows from table' +
      ' id {table}. All identifiers must be provided every time the relations are' +
      ' updated. If an empty array is provided all relations will be deleted.',
    number: 'Accepts a number.',
    numberPositive: 'Accepts a positive number.',
    decimal: 'Accepts a decimal with {places} decimal places after the dot.',
    decimalPositive:
      'Accepts a positive decimal with {places} decimal places after the dot.',
    boolean: 'Accepts a boolean.',
    date: 'Accepts a date time in ISO format.',
    dateTime: 'Accepts a date in ISO format.',
    dateResponse: 'The response will be a datetime in ISO format.',
    dateTimeResponse: 'The response will be a date in ISO format.',
    lastModifiedReadOnly: 'The last modified field is a read only field.',
    createdOnReadOnly: 'The created on field is a read only field.',
    url: 'Accepts a string that must be a URL.',
    email: 'Accepts a string that must be an email address.',
    file: 'Accepts an array of objects containing at least the name of the user file.',
    singleSelect:
      'Accepts an integer representing the chosen select option id or null if none' +
      ' is selected.',
    multipleSelect:
      'Accepts an array of integers each representing the chosen select option id.',
    phoneNumber:
      'Accepts a phone number which has a maximum length of 100 characters' +
      ' consisting solely of digits, spaces and the following characters: ' +
      'Nx,._+*()#=;/- .',
    formula:
      'A read-only field defined by a formula written in the Baserow formula' +
      ' language.',
  },
  viewFilter: {
    contains: 'contains',
    containsNot: 'contains not',
    filenameContains: 'filename contains',
    has: 'has',
    hasNot: 'has not',
    higherThan: 'higher than',
    is: 'is',
    isNot: 'is not',
    isEmpty: 'is empty',
    isNotEmpty: 'is not empty',
    isDate: 'is date',
    isBeforeDate: 'is before date',
    isAfterDate: 'is after date',
    isNotDate: 'is not date',
    isToday: 'is today',
    inThisMonth: 'in this month',
    inThisYear: 'in this year',
    lowerThan: 'lower than',
  },
  viewType: {
    grid: 'Grid',
    form: 'Form',
  },
  premium: {
    deactivated: 'Available in premium version',
  },
  trashType: {
    group: 'group',
    application: 'application',
    table: 'table',
    field: 'field',
    row: 'row',
  },
  clientHandler: {
    notFoundTitle: '{name} not found.',
    notFoundDescription:
      "The selected {name} wasn't found, maybe it has already been deleted.",
    networkErrorTitle: 'Network error',
    networkErrorDescription: 'Could not connect to the API server.',
    tooManyRequestsTitle: 'Too many requests',
    tooManyRequestsDescription:
      'You are sending too many requests to the server. Please wait a moment.',
    notCompletedTitle: 'Action not completed.',
    notCompletedDescription:
      "The action couldn't be completed because an unknown error has occured.",
    userNotInGroupTitle: 'Action not allowed.',
    userNotInGroupDescription:
      "The action couldn't be completed because you aren't a member of the related group.",
    invalidGroupPermissionsTitle: 'Action not allowed.',
    invalidGroupPermissionsDescription:
      "The action couldn't be completed because you don't have the right permissions to the related group.",
    tableDoesNotExistTitle: "Table doesn't exist.",
    tableDoesNotExistDescription:
      "The action couldn't be completed because the related table doesn't exist anymore.",
    rowDoesNotExistTitle: "Row doesn't exist.",
    rowDoesNotExistDescription:
      "The action couldn't be completed because the related row doesn't exist anymore.",
    fileSizeTooLargeTitle: 'File to large',
    fileSizeTooLargeDescription: 'The provided file is too large.',
    invalidFileTitle: 'Invalid file',
    invalidFileDescription: 'The provided file is not a valid file.',
    fileUrlCouldNotBeReachedTitle: 'Invalid URL',
    fileUrlCouldNotBeReachedDescription:
      'The provided file URL could not be reached.',
    invalidFileUrlTitle: 'Invalid URL',
    invalidFileUrlDescription:
      'The provided file URL is invalid or not allowed.',
    adminCannotDeactivateSelfTitle: 'Action not allowed.',
    adminCannotDeactivateSelfDescription:
      'You cannot de-activate or un-staff yourself.',
    adminCannotDeleteSelfTitle: 'Action not allowed.',
    adminCannotDeleteSelfDescription: 'You cannot delete yourself.',
    maxFieldCountExceededTitle: "Couldn't create field.",
    maxFieldCountExceededDescription:
      "The action couldn't be completed because the field count exceeds the limit",
    cannotRestoreParentBeforeChildTitle: 'Please restore the parent first.',
    cannotRestoreParentBeforeChildDescription:
      'You cannot restore this item because it depends on a deleted item. Please restore the parent item first.',
    groupUserIsLastAdminTitle: "Can't leave the group",
    groupUserIsLastAdminDescription:
      "It's not possible to leave the group because you're the last admin. Please delete the group or give another user admin permissions.",
  },
  importerType: {
    csv: 'Import a CSV file',
    paste: 'Paste table data',
    xml: 'Import an XML file',
    json: 'Import a JSON file',
  },
  exporterType: {
    csv: 'Export to CSV',
  },
}
