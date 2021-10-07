<template>
  <Modal :tiny="true" :close-button="false">
    <h3>
      <template v-if="selectedIsTrashed">{{
        $t('trashEmptyModal.titleIsTrashed', { name })
      }}</template>
      <template v-else>{{
        $t('trashEmptyModal.titleIsNotTrashed', { name })
      }}</template>
    </h3>
    <p>
      <template v-if="selectedIsTrashed">{{
        $t('trashEmptyModal.messageIsTrashed')
      }}</template>
      <template v-else>{{
        $t('trashEmptyModal.messageIsNotTrashed')
      }}</template>
    </p>
    <div class="actions">
      <ul class="action__links">
        <li>
          <a @click.prevent="hide()">{{ $t('action.cancel') }}</a>
        </li>
      </ul>
      <a class="button button button--error" @click.prevent="emitEmptyAndClose">
        <template v-if="selectedIsTrashed">{{
          $t('trashEmptyModal.buttonIsTrashed')
        }}</template>
        <template v-else>{{
          $t('trashEmptyModal.buttonIsNotTrashed')
        }}</template>
      </a>
    </div>
  </Modal>
</template>

<script>
/**
 * A simple confirmation modal to check that the user is sure they want to permanently
 * delete / empty.
 */
import modal from '@baserow/modules/core/mixins/modal'

export default {
  name: 'TrashEmptyModal',
  components: {},
  mixins: [modal],
  props: {
    name: {
      type: String,
      required: true,
    },
    selectedIsTrashed: {
      type: Boolean,
      required: true,
    },
  },
  methods: {
    emitEmptyAndClose() {
      this.$emit('empty')
      this.hide()
    },
  },
}
</script>

<i18n>
{
  "en": {
    "trashEmptyModal": {
      "titleIsTrashed": "Are you sure you want to permanently delete {name}?",
      "titleIsNotTrashed": "Are you sure you want to empty the trash of {name}?",
      "messageIsTrashed": "This will permanently delete it and all of its contents. After which they cannot be recovered.",
      "messageIsNotTrashed": "This will permanently delete the listed items. After which they cannot be recovered.",
      "buttonIsTrashed": "Permanently delete",
      "buttonIsNotTrashed": "Empty"
    }
  },
  "fr": {
    "trashEmptyModal": {
      "titleIsTrashed": "Êtes-vous sûr·e de vouloir supprimer définitivement {name} ?",
      "titleIsNotTrashed": "Êtes-vous sûr·e de vouloir vider la corbeille de {name} ?",
      "messageIsTrashed": "Cette action va le supprimer définitivement ainsi que tout contenu. Vous ne serez plus en mesure de le restaurer.",
      "messageIsNotTrashed": "Cette action va supprimer définitivement les éléments listés. Vous ne serez plus en mesure de les restaurer.",
      "buttonIsTrashed": "Supprimer définitivement",
      "buttonIsNotTrashed": "Vider"
    }
  }
}
</i18n>
