<template>
  <div class="dashboard__group">
    <div class="dashboard__group-head">
      <div
        ref="contextLink"
        class="dashboard__group-title"
        :class="{ 'dashboard__group-title-link--loading': group._.loading }"
      >
        <Editable
          ref="rename"
          :value="group.name"
          @change="renameGroup(group, $event)"
        ></Editable>
        <a
          class="dashboard__group-title-options"
          @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 0)"
        >
          <i class="dashboard__group-title-icon fas fa-caret-down"></i>
        </a>
      </div>
      <GroupContext
        ref="context"
        :group="group"
        @rename="enableRename()"
      ></GroupContext>
      <a
        v-if="group.permissions === 'ADMIN'"
        class="dashboard__group-link"
        @click="$refs.context.showGroupMembersModal()"
        >Members</a
      >
    </div>
    <ul class="dashboard__group-items">
      <li
        v-for="application in getAllOfGroup(group)"
        :key="application.id"
        class="dashboard__group-item"
      >
        <a
          class="dashboard__group-item-link"
          @click="selectApplication(application)"
        >
          <div class="dashboard__group-item-icon">
            <i class="fas" :class="'fa-' + application._.type.iconClass"></i>
          </div>
          <div class="dashboard__group-item-name">
            {{ application.name }}
          </div>
        </a>
      </li>
      <li class="dashboard__group-item">
        <a
          ref="createApplicationContextLink"
          class="dashboard__group-item-link"
          @click="
            $refs.createApplicationContext.toggle(
              $refs.createApplicationContextLink
            )
          "
        >
          <div
            class="dashboard__group-item-icon dashboard__group-item-icon--add"
          >
            <i class="fas fa-plus"></i>
          </div>
          <div class="dashboard__group-item-name">Create new</div>
        </a>
        <CreateApplicationContext
          ref="createApplicationContext"
          :group="group"
        ></CreateApplicationContext>
      </li>
    </ul>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import CreateApplicationContext from '@baserow/modules/core/components/application/CreateApplicationContext'
import GroupContext from '@baserow/modules/core/components/group/GroupContext'
import editGroup from '@baserow/modules/core/mixins/editGroup'

export default {
  components: {
    CreateApplicationContext,
    GroupContext,
  },
  mixins: [editGroup],
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      getAllOfGroup: 'application/getAllOfGroup',
    }),
  },
  methods: {
    selectApplication(application) {
      const type = this.$registry.get('application', application.type)
      type.select(application, this)
    },
  },
}
</script>
