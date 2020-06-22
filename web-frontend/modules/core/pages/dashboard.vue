<template>
  <div class="layout__col-3-scroll">
    <div v-if="groups.length === 0" class="placeholder">
      <div class="placeholder__icon">
        <i class="fas fa-layer-group"></i>
      </div>
      <h1 class="placeholder__title">No groups found</h1>
      <p class="placeholder__content">
        You aren’t a member of any group. Applications like databases belong to
        a group, so in order to create them you need to create a group.
      </p>
      <div class="placeholder__action">
        <a class="button button--large" @click="$refs.createGroupModal.show()">
          <i class="fas fa-plus"></i>
          Create group
        </a>
      </div>
    </div>
    <div v-if="groups.length > 0" class="dashboard">
      <DashboardGroup
        v-for="group in groups"
        :key="group.id"
        :group="group"
      ></DashboardGroup>
      <div>
        <a class="button button--large" @click="$refs.createGroupModal.show()">
          <i class="fas fa-plus"></i>
          Create group
        </a>
      </div>
    </div>
    <CreateGroupModal ref="createGroupModal"></CreateGroupModal>
  </div>
</template>

<script>
import { mapState } from 'vuex'

import CreateGroupModal from '@baserow/modules/core/components/group/CreateGroupModal'
import DashboardGroup from '@baserow/modules/core/components/group/DashboardGroup'

export default {
  layout: 'app',
  components: { CreateGroupModal, DashboardGroup },
  computed: {
    ...mapState({
      user: (state) => state.auth.user,
      groups: (state) => state.group.items,
      applications: (state) => state.application.items,
    }),
  },
  head() {
    return {
      title: 'Dashboard',
    }
  },
}
</script>
