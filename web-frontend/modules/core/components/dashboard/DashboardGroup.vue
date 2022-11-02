<template>
  <div class="dashboard__group">
    <div class="dashboard__group-head">
      <div
        class="dashboard__group-title"
        :class="{ 'dashboard__group-title--loading': group._.loading }"
      >
        <Editable
          ref="rename"
          :value="group.name"
          @change="renameGroup(group, $event)"
        ></Editable>
        <a
          ref="contextLink"
          class="dashboard__group-title-options"
          @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
        >
          <i class="dashboard__group-title-icon fas fa-caret-down"></i>
        </a>
      </div>
      <GroupContext
        ref="context"
        :group="group"
        @rename="enableRename()"
      ></GroupContext>
      <div class="dashboard__group-title-extra">
        <component
          :is="component"
          v-for="(component, index) in dashboardGroupExtraComponents"
          :key="index"
          :group="group"
          :component-arguments="componentArguments"
        ></component>
      </div>
    </div>
    <component
      :is="component"
      v-for="(component, index) in dashboardGroupComponents"
      :key="index"
      :group="group"
      :component-arguments="componentArguments"
    ></component>
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

          <div class="dashboard__group-item-name">
            {{ $t('dashboardGroup.createApplication') }}
          </div>
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
    componentArguments: {
      type: Object,
      required: true,
    },
  },
  computed: {
    dashboardGroupExtraComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getDashboardGroupExtraComponent())
        .filter((component) => component !== null)
    },
    dashboardGroupComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getDashboardGroupComponent())
        .filter((component) => component !== null)
    },
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
