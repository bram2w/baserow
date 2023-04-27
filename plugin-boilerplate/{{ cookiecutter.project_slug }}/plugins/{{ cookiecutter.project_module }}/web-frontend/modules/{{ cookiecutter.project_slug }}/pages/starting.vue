<template>
  <div>Starting example!</div>
</template>

<script>
export default {
  async asyncData({ app }) {
    const response = await app.$client.get(
      '{{ cookiecutter.project_module }}/starting/'
    )
    return response.data
  },
  head() {
    return {
      title: this.title,
    }
  },
}
</script>
