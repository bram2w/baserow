<template>
  <div class="element__menu">
    <div
      v-if="isDuplicating"
      class="loading element__menu-duplicate-loading"
    ></div>
    <a v-else class="element__menu-item" @click="$emit('duplicate')">
      <i class="fas fa-copy"></i>
      <span class="element__menu-item-description">
        {{ $t('action.duplicate') }}
      </span>
    </a>
    <a
      class="element__menu-item"
      :class="{ disabled: moveUpDisabled }"
      @click="!moveUpDisabled && $emit('move', PLACEMENTS.BEFORE)"
    >
      <i class="fas fa-arrow-up"></i>
      <span v-if="!moveUpDisabled" class="element__menu-item-description">
        {{ $t('elementMenu.moveUp') }}
      </span>
    </a>
    <a
      class="element__menu-item"
      :class="{ disabled: moveDownDisabled }"
      @click="!moveDownDisabled && $emit('move', PLACEMENTS.AFTER)"
    >
      <i class="fas fa-arrow-down"></i>
      <span v-if="!moveDownDisabled" class="element__menu-item-description">
        {{ $t('elementMenu.moveDown') }}
      </span>
    </a>
    <a class="element__menu-item" @click="$emit('delete')">
      <i class="fas fa-trash"></i>
      <span class="element__menu-item-description">
        {{ $t('action.delete') }}
      </span>
    </a>
  </div>
</template>

<script>
import { PLACEMENTS } from '@baserow/modules/builder/enums'

export default {
  name: 'ElementMenu',
  props: {
    moveUpDisabled: {
      type: Boolean,
      required: false,
      default: false,
    },
    moveDownDisabled: {
      type: Boolean,
      required: false,
      default: false,
    },
    isDuplicating: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    PLACEMENTS: () => PLACEMENTS,
  },
}
</script>
