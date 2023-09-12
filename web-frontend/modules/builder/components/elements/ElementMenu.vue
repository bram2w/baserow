<template>
  <div class="element-preview__menu">
    <div
      v-if="isDuplicating"
      class="loading element-preview__menu-duplicate-loading"
    ></div>
    <a v-else class="element-preview__menu-item" @click="$emit('duplicate')">
      <i class="fas fa-copy"></i>
      <span class="element-preview__menu-item-description">
        {{ $t('action.duplicate') }}
      </span>
    </a>
    <a
      v-if="isPlacementVisible(PLACEMENTS.LEFT)"
      class="element-preview__menu-item"
      :class="{ disabled: isPlacementDisabled(PLACEMENTS.LEFT) }"
      @click="
        !isPlacementDisabled(PLACEMENTS.LEFT) && $emit('move', PLACEMENTS.LEFT)
      "
    >
      <i class="fas fa-arrow-left"></i>
      <span
        v-if="!isPlacementDisabled(PLACEMENTS.LEFT)"
        class="element-preview__menu-item-description"
      >
        {{ $t('elementMenu.moveLeft') }}
      </span>
    </a>
    <a
      v-if="isPlacementVisible(PLACEMENTS.RIGHT)"
      class="element-preview__menu-item"
      :class="{ disabled: isPlacementDisabled(PLACEMENTS.RIGHT) }"
      @click="
        !isPlacementDisabled(PLACEMENTS.RIGHT) &&
          $emit('move', PLACEMENTS.RIGHT)
      "
    >
      <i class="fas fa-arrow-right"></i>
      <span
        v-if="!isPlacementDisabled(PLACEMENTS.RIGHT)"
        class="element-preview__menu-item-description"
      >
        {{ $t('elementMenu.moveRight') }}
      </span>
    </a>
    <a
      v-if="isPlacementVisible(PLACEMENTS.BEFORE)"
      class="element-preview__menu-item"
      :class="{ disabled: isPlacementDisabled(PLACEMENTS.BEFORE) }"
      @click="
        !isPlacementDisabled(PLACEMENTS.BEFORE) &&
          $emit('move', PLACEMENTS.BEFORE)
      "
    >
      <i class="fas fa-arrow-up"></i>
      <span
        v-if="!isPlacementDisabled(PLACEMENTS.BEFORE)"
        class="element-preview__menu-item-description"
      >
        {{ $t('elementMenu.moveUp') }}
      </span>
    </a>
    <a
      v-if="isPlacementVisible(PLACEMENTS.AFTER)"
      class="element-preview__menu-item"
      :class="{ disabled: isPlacementDisabled(PLACEMENTS.AFTER) }"
      @click="
        !isPlacementDisabled(PLACEMENTS.AFTER) &&
          $emit('move', PLACEMENTS.AFTER)
      "
    >
      <i class="fas fa-arrow-down"></i>
      <span
        v-if="!isPlacementDisabled(PLACEMENTS.AFTER)"
        class="element-preview__menu-item-description"
      >
        {{ $t('elementMenu.moveDown') }}
      </span>
    </a>
    <a class="element-preview__menu-item" @click="$emit('delete')">
      <i class="fas fa-trash"></i>
      <span class="element-preview__menu-item-description">
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
    isDuplicating: {
      type: Boolean,
      required: false,
      default: false,
    },
    placements: {
      type: Array,
      required: false,
      default: () => [PLACEMENTS.BEFORE, PLACEMENTS.AFTER],
    },
    placementsDisabled: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  computed: {
    PLACEMENTS: () => PLACEMENTS,
  },
  methods: {
    isPlacementVisible(placement) {
      return this.placements.includes(placement)
    },
    isPlacementDisabled(placement) {
      return this.placementsDisabled.includes(placement)
    },
  },
}
</script>
