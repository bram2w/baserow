<template>
  <div>
    <div class="modal-sidebar__head">
      <div class="modal-sidebar__head-icon-and-name">
        <i class="modal-sidebar__head-icon-and-name-icon fas fa-trash"></i>
        {{ $t('trashSidebar.title') }}
      </div>
    </div>
    <ul class="trash-sidebar__groups">
      <li
        v-for="group in groups"
        :key="'trash-group-' + group.id"
        class="trash-sidebar__group"
        :class="{
          'trash-sidebar__group--active': isSelectedTrashGroup(group),
          'trash-sidebar__group--open': isSelectedTrashGroupApplication(group),
          'trash-sidebar__group--trashed': group.trashed,
        }"
      >
        <a
          class="trash-sidebar__group-link"
          @click="emitIfNotAlreadySelectedTrashGroup(group)"
        >
          {{ group.name || $t('trashSidebar.unnamedGroup', { id: group.id }) }}
        </a>
        <ul class="trash-sidebar__applications">
          <li
            v-for="application in group.applications"
            :key="'trash-application-' + application.id"
            class="trash-sidebar__application"
            :class="{
              'trash-sidebar__application--active': isSelectedApp(application),
              'trash-sidebar__application--trashed':
                group.trashed || application.trashed,
            }"
          >
            <a
              class="trash-sidebar__application-link"
              @click="
                emitIfNotAlreadySelectedTrashApplication(group, application)
              "
              >{{
                application.name || 'Unnamed application ' + application.id
              }}</a
            >
          </li>
        </ul>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'TrashSidebar',
  props: {
    groups: {
      type: Array,
      required: true,
    },
    selectedTrashGroup: {
      type: Object,
      required: false,
      default: null,
    },
    selectedTrashApplication: {
      type: Object,
      required: false,
      default: null,
    },
  },
  methods: {
    isSelectedTrashGroup(group) {
      return (
        group.id === this.selectedTrashGroup.id &&
        this.selectedTrashApplication === null
      )
    },
    isSelectedTrashGroupApplication(group) {
      return group.applications.some((application) =>
        this.isSelectedApp(application)
      )
    },
    isSelectedApp(app) {
      return (
        this.selectedTrashApplication !== null &&
        app.id === this.selectedTrashApplication.id
      )
    },
    emitIfNotAlreadySelectedTrashGroup(group) {
      if (!this.isSelectedTrashGroup(group)) {
        this.emitSelected({ group })
      }
    },
    emitIfNotAlreadySelectedTrashApplication(group, application) {
      if (!this.isSelectedApp(application)) {
        this.emitSelected({ group, application })
      }
    },
    emitSelected(selected) {
      this.$emit('selected', selected)
    },
  },
}
</script>
