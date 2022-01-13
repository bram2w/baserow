<template>
  <div class="api-docs__item">
    <div class="api-docs__left">
      <h2 id="section-introduction" class="api-docs__heading-2">
        {{ $t('apiDocs.intro') }}
      </h2>
      <p class="api-docs__content">
        {{ $t('apiDocsIntro.intro', database) }}
      </p>
      <p class="api-docs__content">
        {{ $t('apiDocsIntro.autoDocDescription') }}
      </p>
      <p class="api-docs__content">
        {{ $t('apiDocsIntro.databaseId') }}
        <code class="api-docs__code">{{ database.id }}</code>
        <br />
        {{ $t('apiDocsIntro.jsClient') }}
        <a href="https://github.com/axios/axios" target="_blank">axios</a>
        <br />
        {{ $t('apiDocsIntro.pythonClient') }}
        <a href="https://requests.readthedocs.io/en/master/" target="_blank"
          >requests</a
        >
      </p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'APIDocsIntro',
  props: { database: { type: Object, required: true } },
}
</script>

<i18n>
{
  "en": {
    "apiDocsIntro":{
      "intro": "The {name} database provides an easy way to integrate the data with any external system. The API follows REST semantics, uses JSON to encode objects and relies on standard HTTP codes, machine and human readable errors to signal operation outcomes.",
      "autoDocDescription": "This documentation is generated automatically based on the tables and fields that are in your database. If you make changes to your database, table or fields it could be that the API interface has also changed. Therefore, make sure that you update your API implementation accordingly.",
      "databaseId":"The ID of this database is:",
      "jsClient":"Javascript example API client:",
      "pythonClient":"Python example API client:"
    }
  },
  "fr": {
    "apiDocsIntro":{
      "intro": "L'API de la base {name} offre un moyen simple d'intégrer des données provenant d'un système externe. L'API suit les principes d'architecture REST, utilise le format JSON pour encoder les données, s'appuie sur les codes HTTP standards et propose des messages d'erreurs à la fois techniques mais également lisibles par les humains pour signaler les dysfonctionnements.",
      "autoDocDescription": "Cette documentation est générée automatiquement à partir des table et des champs disponibles dans votre basse de données. Si vous effectuez des modifications sur la base, les tables ou bien sur les champs des tables, cela peut également modifier l'API. Par conséquent, assurez-vous de mettre à jour les clients de votre API dans ce cas.",
      "databaseId":"Identifiant de la base :",
      "jsClient":"Client pour les examples de requêtes en Javascript :",
      "pythonClient":"Client pour les examples de requêtes en Python :"
    }
  }
}
</i18n>
