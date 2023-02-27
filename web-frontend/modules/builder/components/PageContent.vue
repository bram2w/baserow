<template>
  <div>
    <h1>Demo page {{ application.hostname }}</h1>
    <h2>{{ path }} {{ JSON.stringify(params) }}</h2>
    <p>{{ page.content }}</p>
    <nuxt-link
      :to="{ name: 'application-builder-page', params: { pathMatch: '/' } }"
    >
      / (root)
    </nuxt-link>
    |
    <nuxt-link
      :to="{
        name: 'application-builder-page',
        params: { pathMatch: '/test/' },
      }"
    >
      /test/
    </nuxt-link>
    |
    <nuxt-link
      :to="{
        name: 'application-builder-page',
        params: { pathMatch: '/test/17' },
      }"
    >
      /test/17
    </nuxt-link>
    |
    <nuxt-link
      :to="{
        name: 'application-builder-page',
        params: { pathMatch: '/foo/12' },
      }"
    >
      /foo/12
    </nuxt-link>
    |
    <nuxt-link
      :to="{
        name: 'application-builder-page',
        params: { pathMatch: '/foo/42' },
      }"
    >
      /foo/42 (trigger an error)
    </nuxt-link>
    |
    <nuxt-link
      :to="{
        name: 'application-builder-page',
        params: { pathMatch: '/notfound' },
      }"
    >
      Not found
    </nuxt-link>
  </div>
</template>

<script>
export default {
  props: {
    application: {
      type: Object,
      required: true,
    },
    page: {
      type: Object,
      required: true,
    },
    path: {
      type: String,
      required: true,
    },
    params: {
      type: Object,
      required: true,
    },
  },
  mounted() {
    if (this.path === '/foo/42') {
      throw new Error('42 is not the right answer')
    }
  },
}
</script>
