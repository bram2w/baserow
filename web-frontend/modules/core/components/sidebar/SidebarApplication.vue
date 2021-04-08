<template>
  <li
    class="tree__item"
    :class="{
      active: application._.selected,
      'tree__item--loading': application._.loading,
    }"
  >
    <div class="tree__action tree__action--has-options">
      <a class="tree__link" @click="$emit('selected', application)">
        <i
          class="tree__icon tree__icon--type fas"
          :class="'fa-' + application._.type.iconClass"
        ></i>
        <Editable
          ref="rename"
          :value="application.name"
          @change="renameApplication(application, $event)"
        ></Editable>
      </a>
      <a
        ref="contextLink"
        class="tree__options"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
      >
        <i class="fas fa-ellipsis-v"></i>
      </a>
      <Context ref="context">
        <div class="context__menu-title">{{ application.name }}</div>
        <ul class="context__menu">
          <slot name="context"></slot>
          <li>
            <a @click="enableRename()">
              <i class="context__menu-icon fas fa-fw fa-pen"></i>
              Rename {{ application._.type.name | lowercase }}
            </a>
          </li>
          <li>
            <a @click="deleteApplication()">
              <i class="context__menu-icon fas fa-fw fa-trash"></i>
              Delete {{ application._.type.name | lowercase }}
            </a>
          </li>
        </ul>
        <DeleteApplicationModal
          ref="deleteApplicationModal"
          :application="application"
        />
      </Context>
    </div>
    <slot name="body"></slot>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import DeleteApplicationModal from './DeleteApplicationModal'

export default {
  name: 'SidebarApplication',
  components: { DeleteApplicationModal },
  props: {
    application: {
      type: Object,
      required: true,
    },
  },
  methods: {
    setLoading(application, value) {
      this.$store.dispatch('application/setItemLoading', {
        application,
        value,
      })
    },
    enableRename() {
      this.$refs.context.hide()
      this.$refs.rename.edit()
    },
    async renameApplication(application, event) {
      this.setLoading(application, true)

      try {
        await this.$store.dispatch('application/update', {
          application,
          values: {
            name: event.value,
          },
        })
      } catch (error) {
        this.$refs.rename.set(event.oldValue)
        notifyIf(error, 'application')
      }

      this.setLoading(application, false)
    },
    deleteApplication() {
      this.$refs.context.hide()
      this.$refs.deleteApplicationModal.show()
    },
  },
}
</script>
