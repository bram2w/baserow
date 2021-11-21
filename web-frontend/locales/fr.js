export default {
  common: {
    yes: 'oui',
    no: 'non',
    wrong: 'Une erreur est survenue',
  },
  action: {
    upload: 'Envoyer',
    back: 'Retour',
    backToLogin: "Retour à l'identification",
    signUp: 'Créer un compte',
    signIn: "S'identifier",
    createNew: 'Nouveau',
    create: 'Créer',
    change: 'Changer',
    delete: 'Supprimer',
    rename: 'Renomer',
    add: 'Ajouter',
    makeChoice: 'Choisissez',
    cancel: 'Annuler',
    save: '@TODO',
    retry: '@TODO',
    search: 'Chercher',
    copy: 'Copier',
  },
  adminType: {
    settings: 'Paramètres',
  },
  applicationType: {
    database: 'Base de données',
  },
  settingType: {
    account: 'Informations personnelles',
    password: 'Mot de passe',
    tokens: "Jetons d'API",
  },
  userFileUploadType: {
    file: 'de mon appareil',
    url: "d'une URL",
  },
  field: {
    emailAddress: 'Adresse électronique',
  },
  error: {
    invalidEmail: 'Veuillez entrer une adresse électronique valide.',
    notMatchingPassword: 'Les mots de passe ne correspondent pas.',
    minLength: 'Un minimum de {min} caractères sont attendus ici.',
    maxLength: 'Un maximum de {max} caractères sont attendus ici.',
    minMaxLength:
      'Un minimum de {min} et un maximum def {max} caractères sont attendus ici.',
    requiredField: 'Ce champ est requis.',
  },
  permission: {
    admin: 'Admin',
    adminDescription: 'Peut configurer et éditer les groupes et applications.',
    member: 'Membre',
    memberDescription: 'Peut configurer et éditer les applications.',
  },
  fieldType: {
    singleLineText: 'Texte (une ligne)',
    longText: 'Texte long',
    linkToTable: 'Lien vers une table',
    number: 'Nombre',
    boolean: 'Booléen',
    date: 'Date',
    lastModified: 'Dernière modification',
    createdOn: 'Date de création',
    url: 'URL',
    email: 'Email',
    file: 'Fichier',
    singleSelect: 'Liste déroulante',
    phoneNumber: 'Téléphone',
    formula: 'Formule',
  },
  fieldErrors: {
    invalidNumber: 'Nombre invalide',
    maxDigits: '{max} chiffres sont autorisés.',
    invalidUrl: 'URL invalide',
    max254Chars: '254 caractères maximum',
    invalidEmail: 'Adresse email invalide',
    invalidPhoneNumber: 'Num. téléphone invalide',
  },
  fieldDocs: {
    readOnly: 'Ce champ est en lecture seule.',
    text: 'Accepte une seule ligne de texte.',
    longText: 'Accepte un texte multi-ligne.',
    linkRow:
      'Accepte un tableau contenant les identifiants des lignes ' +
      "provenant de la table d'identifiant {table}. Tous les identifiants " +
      'doivent être fournis à chaque fois que les relations sont modifiées. ' +
      'Si une liste vide est fournie, toutes les relations seront supprimées.',
    number: 'Accepte un entier.',
    numberPositive: 'Accepte un entier positive.',
    decimal: 'Accepte un nombre décimal.',
    decimalPositive: 'Accepte un nombre décimal positif.',
    boolean: 'Accepte une valeur booléenne.',
    date: 'Accepte une date au format ISO.',
    dateTime: 'Accepte une date/heure au format ISO.',
    dateResponse: 'La réponse sera une date au format ISO.',
    dateTimeResponse: 'La réponse sera une date/heure au format ISO.',
    lastModifiedReadOnly:
      'La date de modification de la ligne en lecture seule.',
    createdOnReadOnly: 'La date de modification de la ligne en lecture seule.',
    url: 'Accept une URL valide.',
    email: 'Accepte une adresse email valide.',
    file: "Accept un tableau d'objet contenant au moins le nom du fichier utilisateur.",
    singleSelect:
      "Accepte un entier correspondant à l'identifiant de l'option sélectionnée " +
      'ou null si vide.',
    multipleSelect:
      "Accepte un tableau d'entier correspondant chacun à l'identifiant " +
      "d'une valeur sélectionnée.",
    phoneNumber:
      "Accepte un numéro  de téléphone d'une longueur maximum de 100 caractères " +
      'qui doivent être des chiffres, des espaces ou les caractères suivants : ' +
      'Nx,._+*()#=;/- .',
    formula:
      'Un champ en lecture seule défini par une formule rédigée ' +
      'dans le format spécifique de Baserow.',
  },
  viewFilter: {
    contains: 'contient',
    containsNot: 'ne contient pas',
    filenameContains: 'nom du fichier contient',
    has: 'est',
    hasNot: "n'est pas",
    higherThan: 'plus grand que',
    is: 'est',
    isNot: "n'est pas",
    isEmpty: 'est vide',
    isNotEmpty: "n'est pas vide",
    isDate: 'est égal',
    isBeforeDate: 'est avant',
    isAfterDate: 'est après',
    isNotDate: 'est différent',
    isToday: "est aujourd'hui",
    inThisMonth: 'ce mois-ci',
    inThisYear: 'cette année',
    lowerThan: 'plus petit que',
  },
  viewType: {
    grid: 'Tableau',
    form: 'Formulaire',
  },
  premium: {
    deactivated: 'Désactivé',
  },
  trashType: {
    group: 'groupe',
    application: 'application',
    table: 'table',
    field: 'champ',
    row: 'ligne',
  },
  webhook: {
    request: '@TODO',
    response: '@TODO',
    successfullyUpdated: '@TODO',
    status: {
      noStatus: '@TODO',
      statusOK: '@TODO',
      statusNotOK: '@TODO',
    },
    eventType: {
      rowCreated: '@TODO',
      rowUpdated: '@TODO',
      rowDeleted: '@TODO',
    },
  },
  clientHandler: {
    notFoundTitle: "L'élément {name} n'a pas été trouvé",
    notFoundDescription:
      "L'élément {name} sélectionné n'a pas été trouvé. Peut-être qu'il a déjà été supprimé.",
    networkErrorTitle: 'Erreur de connection',
    networkErrorDescription:
      'Connection impossible avec le serveur. Veuillez vérifier votre connection.',
    tooManyRequestsTitle: 'Trop de requêtes',
    tooManyRequestsDescription:
      'Vous envoyez trop de requêtes au serveur. Veuillez patienter avant de recommencer.',
    notCompletedTitle: "Échec de l'action",
    notCompletedDescription:
      "L'action n'a pas pu aboutir pour une raison inconnue.",
    userNotInGroupTitle: 'Action interdite',
    userNotInGroupDescription:
      "L'action n'a pas pu aboutir car vous n'êtes pas membre du groupe associé.",
    invalidGroupPermissionsTitle: 'Action interdite',
    invalidGroupPermissionsDescription:
      "L'action n'a pas pu aboutir car vous n'avez pas les permissions nécessaires dans le groupe associé.",
    tableDoesNotExistTitle: "La table n'existe pas",
    tableDoesNotExistDescription:
      "L'action n'a pas pu aboutir car la table concernée n'existe plus.",
    rowDoesNotExistTitle: "La ligne n'existe pas",
    rowDoesNotExistDescription:
      "L'action n'a pas pu aboutir car la ligne concernée n'existe plus",
    fileSizeTooLargeTitle: 'Fichier trop volumineux',
    fileSizeTooLargeDescription: 'Le fichier fourni est trop volumineux.',
    invalidFileTitle: 'Fichier invalide',
    invalidFileDescription: "Le fichier fourni n'est pas un fichier valide.",
    fileUrlCouldNotBeReachedTitle: 'URL invalide',
    fileUrlCouldNotBeReachedDescription: "L'URL fournie n'est pas accessible.",
    invalidFileUrlTitle: 'URL invalide',
    invalidFileUrlDescription:
      "L'URL fournie n'est pas valide ou est protégée.",
    adminCannotDeactivateSelfTitle: 'Action interdite',
    adminCannotDeactivateSelfDescription:
      "Vous ne pouvez pas désactiver votre compte ou modifier votre appartenance à l'équipe staff.",
    adminCannotDeleteSelfTitle: 'Action interdite',
    adminCannotDeleteSelfDescription:
      'Vous ne pouvez pas supprimer votre propre compte utilisateur.',
    maxFieldCountExceededTitle: 'Impossible de créer une colonne',
    maxFieldCountExceededDescription:
      "L'action n'a pas pu aboutir car vous avez atteint le nombre maximum de colonne pour cette table.",
    cannotRestoreParentBeforeChildTitle:
      "Veuillez restaurer l'élément parent d'abord",
    cannotRestoreParentBeforeChildDescription:
      "Vous ne pouvez pas restaurer cet élément car il dépend d'un autre élément supprimé. Vous devez restaurer l'élément parent avant de pouvoir restaurer cet élément",
    groupUserIsLastAdminTitle: 'Impossible de quitter le groupe',
    groupUserIsLastAdminDescription:
      "Il est impossible de quitter ce groupe car vous en êtes le dernier administrateur. Veuillez supprimer le groupe ou donner les droits d'administration à un autre utilisateur.",
  },
  importerType: {
    csv: 'Importer un fichier CSV',
    paste: 'Coller des données tabulaires',
    xml: 'Importer un fichier XML',
    json: 'Importer un fichier JSON',
  },
  exporterType: {
    csv: 'Exporter vers CSV',
  },
}
