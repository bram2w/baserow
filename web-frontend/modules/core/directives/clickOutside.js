import { onClickOutside } from '@baserow/modules/core/utils/dom'

export default {
  bind(el, binding, vnode) {
    el.onClickOutsideEventCancelDirective = onClickOutside(el, (target) => {
      vnode.context[binding.expression](target)
    })
  },
  unbind(el) {
    el.onClickOutsideEventCancelDirective()
  },
}
