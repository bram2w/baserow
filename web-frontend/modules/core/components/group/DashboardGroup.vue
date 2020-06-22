<template>
  <div class="dashboard__group">
    <h2 class="dashboard__group-title">
      <a
        ref="contextLink"
        class="dashboard__group-title-link"
        :class="{ 'dashboard__group-title-link--loading': group._.loading }"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'left', 0)"
      >
        <Editable
          ref="rename"
          :value="group.name"
          @change="renameGroup(group, $event)"
        ></Editable>
        <i class="dashboard__group-title-icon fas fa-caret-down"></i>
      </a>
      <Context ref="context">
        <ul class="context__menu">
          <li>
            <a @click="enableRename()">
              <i class="context__menu-icon fas fa-fw fa-pen"></i>
              Rename group
            </a>
          </li>
          <li>
            <a @click="deleteGroup(group)">
              <i class="context__menu-icon fas fa-fw fa-trash"></i>
              Delete group
            </a>
          </li>
        </ul>
      </Context>
    </h2>
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
import editGroup from '@baserow/modules/core/mixins/editGroup'

export default {
  components: { CreateApplicationContext },
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
