<template>
  <div class="element-preview__menu" @click.stop>
    <span v-if="isDuplicating" class="element-preview__menu-item disabled">
      <div class="loading"></div>
    </span>
    <a v-else class="element-preview__menu-item" @click="$emit('duplicate')">
      <i class="iconoir-copy"></i>
      <span class="element-preview__menu-item-description">
        {{ $t('action.duplicate') }} (d)
      </span>
    </a>
    <a
      v-if="hasParent"
      class="element-preview__menu-item"
      @click="$emit('select-parent')"
    >
      <i class="iconoir-scale-frame-enlarge"></i>
      <span class="element-preview__menu-item-description">
        {{ $t('elementMenu.selectParent') }} (p)
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
      <i class="iconoir-nav-arrow-left"></i>
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
      <i class="iconoir-nav-arrow-right"></i>
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
      <i class="iconoir-nav-arrow-up"></i>
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
      <i class="iconoir-nav-arrow-down"></i>
      <span
        v-if="!isPlacementDisabled(PLACEMENTS.AFTER)"
        class="element-preview__menu-item-description"
      >
        {{ $t('elementMenu.moveDown') }}
      </span>
    </a>
    <a class="element-preview__menu-item" @click="$emit('delete')">
      <i class="iconoir-bin"></i>
      <span class="element-preview__menu-item-description">
        {{ $t('action.delete') }} (del)
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
    hasParent: {
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
