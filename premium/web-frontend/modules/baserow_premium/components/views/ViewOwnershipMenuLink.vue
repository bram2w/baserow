<template>
  <li class="context__menu-item">
    <a
      class="context__menu-item-link"
      @click="changeOwnershipType(view.ownership_type)"
    >
      <i class="context__menu-item-icon iconoir-right-round-arrow"></i>
      {{ changeOwnershipTypeText }}
    </a>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import { CollaborativeViewOwnershipType } from '@baserow/modules/database/viewOwnershipTypes'
import { PersonalViewOwnershipType } from '@baserow_premium/viewOwnershipTypes'

export default {
  name: 'ViewOwnershipMenuLink',
  props: {
    view: {
      type: Object,
      required: true,
    },
  },
  computed: {
    changeOwnershipTypeOptions() {
      const collaborativeOwnershipType =
        new CollaborativeViewOwnershipType().getType()
      const personalOwnershipType = new PersonalViewOwnershipType().getType()

      return {
        [collaborativeOwnershipType]: {
          text: this.$t('viewContext.toPersonal'),
          targetType: personalOwnershipType,
        },
        [personalOwnershipType]: {
          text: this.$t('viewContext.toCollaborative'),
          targetType: collaborativeOwnershipType,
        },
      }
    },
    changeOwnershipTypeText() {
      return this.changeOwnershipTypeOptions[this.view.ownership_type].text
    },
  },
  methods: {
    async changeOwnershipType() {
      const targetType =
        this.changeOwnershipTypeOptions[this.view.ownership_type].targetType
      try {
        await this.$store.dispatch('view/update', {
          view: this.view,
          values: { ownership_type: targetType },
        })
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
  },
}
</script>
