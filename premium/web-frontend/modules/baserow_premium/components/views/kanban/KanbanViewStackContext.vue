<template>
  <Context>
    <ul class="context__menu">
      <li>
        <a @click=";[$emit('create-row'), hide()]">
          <i class="context__menu-icon fas fa-fw fa-plus"></i>
          {{ $t('kanbanViewStackContext.createCard') }}
        </a>
      </li>
      <li v-if="option !== null">
        <a
          ref="updateContextLink"
          @click="$refs.updateContext.toggle($refs.updateContextLink)"
        >
          <i class="context__menu-icon fas fa-fw fa-pen"></i>
          {{ $t('kanbanViewStackContext.editStack') }}
        </a>
        <KanbanViewUpdateStackContext
          ref="updateContext"
          :option="option"
          :fields="fields"
          :primary="primary"
          :store-prefix="storePrefix"
          @saved="hide()"
        ></KanbanViewUpdateStackContext>
      </li>
      <li v-if="option !== null">
        <a @click="$refs.deleteModal.show()">
          <i class="context__menu-icon fas fa-fw fa-trash-alt"></i>
          {{ $t('kanbanViewStackContext.deleteStack') }}
        </a>
      </li>
    </ul>
    <Modal v-if="option !== null" ref="deleteModal">
      <h2 class="box__title">
        {{ $t('kanbanViewStackContext.delete', { name: option.value }) }}
      </h2>
      <Error :error="error"></Error>
      <div>
        <p>
          {{
            $t('kanbanViewStackContext.deleteDescription', {
              name: option.value,
            })
          }}
        </p>
        <div class="actions">
          <div class="align-right">
            <a
              class="button button--large button--error"
              :class="{ 'button--loading': loading }"
              :disabled="loading"
              @click="deleteStack()"
            >
              {{ $t('kanbanViewStackContext.delete', { name: option.value }) }}
            </a>
          </div>
        </div>
      </div>
    </Modal>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import error from '@baserow/modules/core/mixins/error'
import KanbanViewUpdateStackContext from '@baserow_premium/components/views/kanban/KanbanViewUpdateStackContext'

export default {
  name: 'KanbanViewStackContext',
  components: { KanbanViewUpdateStackContext },
  mixins: [context, error],
  props: {
    option: {
      validator: (prop) => typeof prop === 'object' || prop === null,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    primary: {
      type: Object,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    async deleteStack() {
      this.loading = true

      try {
        const doUpdate = await this.$store.dispatch(
          this.storePrefix + 'view/kanban/deleteStack',
          {
            optionId: this.option.id,
            fields: this.fields,
            primary: this.primary,
            deferredFieldUpdate: true,
          }
        )
        await this.$emit('refresh', {
          callback: () => {
            doUpdate()
            this.loading = false
          },
        })
      } catch (error) {
        this.handleError(error)
        this.loading = false
      }
    },
  },
}
</script>

<i18n>
{
  "en": {
    "kanbanViewStackContext": {
      "createCard": "Create card",
      "editStack": "Edit stack",
      "deleteStack": "Delete stack",
      "delete": "Delete {name}",
      "deleteDescription": "Are you sure that you want to delete stack {name}? Deleting the stack results in deleting the select option of the single select field, which might result into data loss because row values are going to be set to empty."
    }
  },
  "fr": {
    "kanbanViewStackContext": {
      "createCard": "Créer une carte",
      "editStack": "Modifier la colonne",
      "deleteStack": "Supprimer la colonne",
      "delete": "Supprimer {name}",
      "deleteDescription": "Êtes-vous sur·e de vouloir supprimer la colonne {name} ? Supprimer une valeur revient à supprimer l'option correspondante de la liste déroulante, ce qui peut impliquer une perte d'information car les lignes contenant cette valeur auront désormais une valeur vide à la place pour ce champ."
    }
  }
}
</i18n>
