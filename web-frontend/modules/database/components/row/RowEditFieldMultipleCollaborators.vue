<template>
  <div class="control__elements">
    <ul class="field-multiple-collaborators__items">
      <li
        v-for="item in value"
        :key="item.id"
        class="
          field-multiple-collaborators__item
          field-multiple-collaborators__item--row-edit
        "
      >
        <template v-if="item.id && item.name">
          <div
            class="
              field-multiple-collaborators__name
              background-color--light-gray
            "
          >
            {{ getCollaboratorName(item) }}
            <a
              v-if="!readOnly"
              class="field-multiple-collaborators__remove"
              @click.prevent="removeValue($event, value, item.id)"
            >
              <i class="fas fa-times"></i>
            </a>
          </div>
          <div class="field-multiple-collaborators__initials">
            {{ getCollaboratorNameInitials(item) }}
          </div>
        </template>
      </li>
    </ul>
    <a
      v-if="!readOnly"
      ref="dropdownLink"
      class="add"
      @click.prevent="toggleDropdown()"
    >
      <i class="fas fa-plus add__icon"></i>
      {{ $t('rowEditFieldMultipleCollaborators.addCollaborator') }}
    </a>
    <FieldCollaboratorDropdown
      v-if="!readOnly"
      ref="dropdown"
      :collaborators="availableCollaborators"
      :disabled="readOnly"
      :show-input="false"
      :show-empty-value="false"
      :class="{ 'dropdown--error': touched && !valid }"
      @input="updateValue($event, value)"
      @hide="touch()"
    ></FieldCollaboratorDropdown>
    <div v-show="touched && !valid" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import collaboratorField from '@baserow/modules/database/mixins/collaboratorField'
import FieldCollaboratorDropdown from '@baserow/modules/database/components/field/FieldCollaboratorDropdown'
import collaboratorName from '@baserow/modules/database/mixins/collaboratorName'

export default {
  name: 'RowEditFieldMultipleCollaborators',
  components: { FieldCollaboratorDropdown },
  mixins: [rowEditField, collaboratorField, collaboratorName],
}
</script>
