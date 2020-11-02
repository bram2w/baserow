<template>
  <Modal>
    <h2 class="box__title">Delete {{ application.name }}</h2>
    <Error :error="error"></Error>
    <div>
      <p>
        Are you sure you want to delete the
        {{ application._.type.name | lowercase }}
        <strong>{{ application.name }}</strong
        >?
        <span v-if="dependents.length > 0"
          >The following {{ dependentsName }}
          <template v-if="dependents.length === 1">is</template>
          <template v-else>are</template>
          also going to be permanently deleted:</span
        >
      </p>
      <div v-if="dependents.length > 0" class="delete-section">
        <div class="delete-section__label">
          <div class="delete-section__label-icon">
            <i class="fas fa-exclamation"></i>
          </div>
          Will also be permanently deleted
        </div>
        <ul class="delete-section__list">
          <li v-for="dependent in dependents" :key="dependent.id">
            <i
              class="delete-section__list-icon fas fa-database"
              :class="'fa-' + dependent.iconClass"
            ></i>
            {{ dependent.name }}
          </li>
        </ul>
      </div>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large button--error"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="deleteApplication()"
          >
            Delete {{ application._.type.name | lowercase }}
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'

export default {
  name: 'DeleteApplicationModal',
  mixins: [modal, error],
  props: {
    application: {
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
    dependentsName() {
      const names = this.$registry
        .get('application', this.application.type)
        .getDependentsName(this.application)
      return this.dependents.length === 1 ? names[0] : names[1]
    },
    dependents() {
      return this.$registry
        .get('application', this.application.type)
        .getDependents(this.application)
    },
  },
  methods: {
    async deleteApplication() {
      this.hideError()
      this.loading = true

      try {
        await this.$store.dispatch('application/delete', this.application)
        this.hide()
      } catch (error) {
        this.handleError(error, 'application')
      }

      this.loading = false
    },
  },
}
</script>
