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
