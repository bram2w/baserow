<template>
  <div>
    <h1>Welcome {{ user }}</h1>
    <p>
      {{ groups }}
      <br /><br />
      {{ selectedGroup }}
      <br /><br />
      {{ applications }}
      <br /><br />
      {{ groupApplications }}
      <br /><br />
      <nuxt-link :to="{ name: 'application-database', params: { id: 1 } }">
        <i class="fas fa-arrow-left"></i>
        App
      </nuxt-link>
    </p>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  layout: 'app',
  computed: {
    ...mapState({
      user: state => state.auth.user,
      groups: state => state.group.items,
      selectedGroup: state => state.group.selected,
      applications: state => state.application.applications,
      groupApplications: state => state.application.items
    })
  }
}
</script>
