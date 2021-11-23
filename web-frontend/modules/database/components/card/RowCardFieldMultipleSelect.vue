<template functional>
  <div class="card-many-to-many__list-wrapper">
    <div class="card-many-to-many__list">
      <div
        v-for="item in props.value"
        :key="item.id"
        class="card-many-to-many__item card-multiple-select-option"
        :class="'background-color--' + item.color"
      >
        <span class="card-many-to-many__name">{{ item.value }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  height: 22,
}
</script>
