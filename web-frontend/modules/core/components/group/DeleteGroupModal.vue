<template>
  <Modal>
    <h2 class="box__title">Delete {{ group.name }}</h2>
    <Error :error="error"></Error>
    <div>
      <p>
        Are you sure you want to delete the group
        <strong>{{ group.name }}</strong
        >?
        <span v-if="applications.length > 0">
          The following
          <template v-if="applications.length == 1"
            >application including its data is</template
          >
          <template v-else>applications including their data are</template>
          going to be permanently deleted:</span
        >
      </p>
      <div v-if="applications.length > 0" class="delete-section">
        <div class="delete-section__label">
          <div class="delete-section__label-icon">
            <i class="fas fa-exclamation"></i>
          </div>
          Will also be permanently deleted
        </div>
        <ul class="delete-section__list">
          <li v-for="application in applications" :key="application.id">
            <i
              class="delete-section__list-icon fas fa-database"
              :class="'fa-' + application._.type.iconClass"
            ></i>
            {{ application.name }}
            <small>{{ getApplicationDependentsText(application) }}</small>
          </li>
        </ul>
      </div>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large button--error"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="deleteGroup()"
          >
            Delete group
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import { mapGetters } from 'vuex'
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'

export default {
  name: 'DeleteGroupModal',
  mixins: [modal, error],
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
    }
  },
  computed: {
    ...mapGetters({
      getAllOfGroup: 'application/getAllOfGroup',
    }),
    applications() {
      return this.getAllOfGroup(this.group)
    },
  },
  methods: {
    async deleteGroup() {
      this.hideError()
      this.loading = true

      try {
        await this.$store.dispatch('group/delete', this.group)
        this.hide()
      } catch (error) {
        this.handleError(error, 'application')
      }

      this.loading = false
    },
    getApplicationDependentsText(application) {
      const dependents = this.$registry
        .get('application', application.type)
        .getDependents(application)
      const names = this.$registry
        .get('application', application.type)
        .getDependentsName(application)
      const name = dependents.length === 1 ? names[0] : names[1]
      return `including ${dependents.length} ${name}`
    },
  },
}
</script>
