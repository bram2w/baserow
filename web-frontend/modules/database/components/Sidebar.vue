<template>
  <div>
    <ul class="tree-subs">
      <li class="tree-sub active">
        <a href="#" class="tree-sub-link">@TODO</a>
        <a
          class="tree-options"
          @click="
            $refs.context.toggle($event.currentTarget, 'bottom', 'right', 0)
          "
        >
          <i class="fas fa-ellipsis-v"></i>
        </a>
        <Context ref="context">
          <div class="context-menu-title">@TODO</div>
          <ul class="context-menu">
            <li>
              <a>
                <i class="context-menu-icon fas fa-fw fa-pen"></i>
                Rename
              </a>
            </li>
            <li>
              <a>
                <i class="context-menu-icon fas fa-fw fa-trash"></i>
                Delete
              </a>
            </li>
          </ul>
        </Context>
      </li>
    </ul>
    <a href="#" class="tree-sub-add">
      <i class="fas fa-plus"></i>
      Create table
    </a>
  </div>
</template>
