<template>
  <div>
    <Notifications></Notifications>
    <div class="style-guide-wrapper">
      <div class="style-guide">
        <div class="margin-bottom-3">
          <h1>&lt;h1&gt;Heading 1&lt;/h1&gt;</h1>
          <h2>&lt;h2&gt;Heading 2&lt;/h2&gt;</h2>
          <h3>&lt;h3&gt;Heading 3&lt;/h3&gt;</h3>
        </div>
        <div class="margin-bottom-3">
          <p>
            Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
            elit. Pellentesque eget ipsum eu risus congue posuere vel at erat.
            Phasellus mattis est sit amet dui sodales, a interdum turpis
            interdum. Sed eu lobortis libero. Phasellus
            <strong>vestibulum</strong>, nunc sed elementum scelerisque, tellus
            felis pretium lectus, eget laoreet quam est in massa. Maecenas non
            dapibus dolor. Mauris <em>condimentum</em> iaculis dui vel finibus.
            Nullam consequat non arcu at vehicula. Maecenas ac consequat ipsum,
            sed viverra dui. Donec dignissim suscipit ultrices. Nullam quis
            mattis nulla, et venenatis justo. Curabitur scelerisque dictum
            <a href="#">velit</a>, eget vestibulum lacus gravida in. Praesent id
            lorem volutpat, venenatis quam vel, ultricies leo.
          </p>
        </div>
        <div class="margin-bottom-3">
          <div class="control">
            <label class="control-label">Small text field</label>
            <div class="control-elements">
              <input type="text" class="input" />
            </div>
          </div>
          <div class="control">
            <label class="control-label">Small with error</label>
            <div class="control-elements">
              <input type="text" class="input input-error" />
              <div class="error">Please do something different</div>
            </div>
          </div>
          <div class="control">
            <label class="control-label">Small text field</label>
            <div class="control-elements">
              <input
                type="text"
                class="input"
                placeholder="Voer hier iets in"
              />
            </div>
          </div>
          <div class="control">
            <label class="control-label">Large text field</label>
            <div class="control-elements">
              <input
                type="text"
                class="input input-large"
                placeholder="Voer hier iets in"
              />
            </div>
          </div>
          <div class="control">
            <label class="control-label">Large password field</label>
            <div class="control-elements">
              <input
                type="password"
                class="input input-large"
                placeholder="Please enter your password"
              />
            </div>
          </div>
          <div class="control">
            <label class="control-label">Checkbox field</label>
            <div class="control-elements">
              value: {{ checkbox }}
              <br />
              <br />
              <Checkbox v-model="checkbox"></Checkbox>
              <Checkbox v-model="checkbox">With text</Checkbox>
            </div>
          </div>
          <div class="control">
            <label class="control-label">Dropdown</label>
            <div class="control-elements">
              value: {{ dropdown }}
              <br />
              <br />
              <div style="width: 200px;">
                <Dropdown v-model="dropdown">
                  <DropdownItem name="Choice 1" value="choice-1"></DropdownItem>
                  <DropdownItem
                    name="Choice 2"
                    value="choice-2"
                    icon="pencil"
                  ></DropdownItem>
                  <DropdownItem
                    name="Choice 3"
                    value="choice-3"
                    icon="database"
                  ></DropdownItem>
                </Dropdown>
              </div>
            </div>
          </div>
        </div>
        <div class="margin-bottom-3">
          <div class="alert alert-has-icon">
            <div class="alert-icon">
              <i class="fas fa-exclamation"></i>
            </div>
            <div class="alert-title">Notification message</div>
            <p class="alert-content">
              Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
              elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui
              ligula. Pellentesque feugiat erat vel porttitor euismod. Duis nec
              viverra urna. Praesent.
            </p>
          </div>
          <div class="alert">
            <div class="alert-title">Notification message</div>
            <p class="alert-content">
              Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
              elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui
              ligula. Pellentesque feugiat erat vel porttitor euismod. Duis nec
              viverra urna. Praesent lobortis feugiat erat, nec volutpat nulla
              tincidunt vel. In hac habitasse platea dictumst. Aenean fringilla
              lacus nunc, non pharetra mauris pulvinar lacinia. Aenean ut sem
              lacinia, sagittis quam sed, pellentesque orci. Aenean non
              consequat mi. Nunc laoreet ligula a nunc eleifend, nec accumsan
              felis euismod.
            </p>
          </div>
          <div class="alert alert-success alert-has-icon">
            <div class="alert-icon">
              <i class="fas fa-exclamation"></i>
            </div>
            <div class="alert-title">Notification message</div>
            <p class="alert-content">
              Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
              elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui
              ligula. Pellentesque feugiat erat vel porttitor euismod. Duis nec
              viverra urna. Praesent.
            </p>
          </div>
          <div class="alert alert-warning alert-has-icon">
            <div class="alert-icon">
              <i class="fas fa-exclamation"></i>
            </div>
            <div class="alert-title">Notification message</div>
            <p class="alert-content">
              Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
              elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui
              ligula. Pellentesque feugiat erat vel porttitor euismod. Duis nec
              viverra urna. Praesent.
            </p>
          </div>
          <div class="alert alert-error alert-has-icon">
            <div class="alert-icon">
              <i class="fas fa-exclamation"></i>
            </div>
            <div class="alert-title">Notification message</div>
            <p class="alert-content">
              Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
              elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui
              ligula. Pellentesque feugiat erat vel porttitor euismod. Duis nec
              viverra urna. Praesent.
            </p>
          </div>
        </div>
        <div class="margin-bottom-3 style-guide-buttons">
          <a class="button">a.button</a>
          <a class="button disabled">a.button[disabled]</a>
          <a class="button button-success">a.button.button-success</a>
          <a class="button button-warning">a.button.button-warning</a>
          <a class="button button-error">a.button.button-error</a>
          <a class="button">
            a.button
            <i class="button-icon fas fa-lock-open"></i>
          </a>
          <a class="button">
            <i class="button-icon fas fa-arrow-left"></i>
            a.button
          </a>
          <a class="button button-ghost">a.button.button-ghosts</a>
          <a class="button">
            <i class="fas fa-user-check"></i>
          </a>
          <a class="button button-ghost">
            <i class="fas fa-user-check"></i>
          </a>
        </div>
        <div class="margin-bottom-3 style-guide-buttons">
          <button class="button">button.button</button>
          <button class="button" disabled>button.button[disabled]</button>
          <button class="button button-success">
            button.button.button-success
          </button>
          <button class="button button-warning">
            button.button.button-warning
          </button>
          <button class="button button-error">
            button.button.button-error
          </button>
          <button class="button">
            button.button
            <i class="button-icon fas fa-lock-open"></i>
          </button>
          <button class="button">
            <i class="button-icon fas fa-arrow-left"></i>
            button.button
          </button>
          <button class="button button-ghost">
            button.button.ghost-button
          </button>
          <button class="button">
            <i class="fas fa-user-check"></i>
          </button>
          <button class="button button-ghost">
            <i class="fas fa-user-check"></i>
          </button>
        </div>
        <div class="margin-bottom-3 style-guide-buttons">
          <a class="button button-large">a.button.button-large</a>
          <a class="button button-large disabled"
            >a.button.disabled.button-large</a
          >
          <a class="button button-large button-success"
            >a.button.button-large.button-success</a
          >
          <a class="button button-large button-warning"
            >a.button.button-large.button-warning</a
          >
          <a class="button button-large button-error"
            >a.button.button-large.button-error</a
          >
          <a class="button button-large">
            a.button.button-large
            <i class="button-icon fas fa-lock-open"></i>
          </a>
          <a class="button button-large">
            <i class="button-icon fas fa-arrow-left"></i>
            a.button.button-large
          </a>
          <a class="button button-large button-ghost">a.button.button-ghosts</a>
          <a class="button button-large">
            <i class="fas fa-user-check"></i>
          </a>
          <a class="button button-large button-ghost">
            <i class="fas fa-user-check"></i>
          </a>
        </div>
        <div class="margin-bottom-3">
          <a class="button button-large button-loading">Loading</a>
          <a class="button button-loading">Loading</a>
        </div>
        <div class="margin-bottom-3 style-guide-contexts">
          <div class="context">
            <div class="context-menu-title">Vehicles</div>
            <ul class="context-menu">
              <li>
                <a href="#">
                  <i class="context-menu-icon fas fa-fw fa-pen"></i>
                  Rename database
                </a>
              </li>
              <li>
                <a href="#">
                  <i class="context-menu-icon fas fa-fw fa-trash"></i>
                  Delete table
                </a>
              </li>
            </ul>
          </div>
          <div class="select">
            <div class="select-search">
              <i class="select-search-icon fas fa-search"></i>
              <input
                type="text"
                class="select-search-input"
                placeholder="Search views"
              />
            </div>
            <ul class="select-items">
              <li class="select-item active">
                <a href="#" class="select-item-link">Group name 1</a>
                <a href="#" class="select-item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
              <li class="select-item">
                <a href="#" class="select-item-link">Group name 2</a>
                <a href="#" class="select-item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
              <li class="select-item select-item-loading">
                <a href="#" class="select-item-link">Group name 3</a>
                <a href="#" class="select-item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
              <li class="select-item">
                <a href="#" class="select-item-link">Group name 4</a>
                <a href="#" class="select-item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
            </ul>
            <div class="select-footer">
              <a href="#" class="select-footer-button">
                <i class="fas fa-plus"></i>
                Do something
              </a>
            </div>
          </div>
          <div class="select">
            <div class="select-search">
              <i class="select-search-icon fas fa-search"></i>
              <input
                type="text"
                class="select-search-input"
                placeholder="Search views"
              />
            </div>
            <ul class="select-items">
              <li class="select-item">
                <a href="#" class="select-item-link">
                  <i class="select-item-icon fas fa-th fa-fw color-primary"></i>
                  Grid view name
                </a>
                <a href="#" class="select-item-options" data-context=".context">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
              <li class="select-item">
                <a href="#" class="select-item-link">
                  <i class="select-item-icon fas fa-th fa-fw color-primary"></i>
                  Grid view option 2.
                </a>
                <a href="#" class="select-item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
              <li class="select-item">
                <a href="#" class="select-item-link">
                  <i class="select-item-icon fas fa-th fa-fw color-primary"></i>
                  Grid view 2
                </a>
                <a href="#" class="select-item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
              <li class="select-item">
                <a href="#" class="select-item-link">
                  <i class="select-item-icon fas fa-th fa-fw color-primary"></i>
                  Grid view 3
                </a>
                <a href="#" class="select-item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
            </ul>
            <div class="select-footer">
              <div class="select-footer-multiple">
                <div class="select-footer-multiple-label">Add a view:</div>
                <a href="#" class="select-footer-multiple-item">
                  <i class="select-footer-multiple-icon fas fa-th"></i>
                  Grid
                </a>
              </div>
            </div>
          </div>
        </div>
        <div class="margin-bottom-3">
          <a class="button" @click="$refs.context1.toggle($event.target)">
            toggle context
            <i class="fas fa-pencil"></i>
          </a>
          <Context ref="context1">
            <div class="context-menu-title">Vehicles</div>
            <ul class="context-menu">
              <li>
                <a href="#">
                  <i class="context-menu-icon fas fa-fw fa-pen"></i>
                  This does nothing
                </a>
              </li>
              <li>
                <a @click="$refs.context2.toggle($event.target)">
                  Open another context
                </a>
                <Context ref="context2">
                  <div class="context-menu-title">Open modal</div>
                  <ul class="context-menu">
                    <li>
                      <a @click="$refs.modal1.show()">
                        <i class="context-menu-icon fas fa-fw fa-pen"></i>
                        Click to open modal
                      </a>
                    </li>
                    <Modal ref="modal1">
                      <h2 class="box-title">Modal inside a context</h2>
                      <a
                        class="button"
                        @click="$refs.context3.toggle($event.target)"
                      >
                        toggle context
                        <i class="fas fa-pencil"></i>
                      </a>
                      <Context ref="context3">
                        <div class="context-menu-title">Vehicles</div>
                        <ul class="context-menu">
                          <li>
                            <a href="#">
                              <i class="context-menu-icon fas fa-fw fa-pen"></i>
                              This does nothing
                            </a>
                          </li>
                          <li>
                            <a @click="$refs.context4.toggle($event.target)">
                              Open another context
                            </a>
                            <Context ref="context4">
                              <div class="context-menu-title">End!</div>
                            </Context>
                          </li>
                          <li>
                            <a href="#">
                              <i
                                class="context-menu-icon fas fa-fw fa-trash"
                              ></i>
                              This does nothing
                            </a>
                          </li>
                        </ul>
                      </Context>
                    </Modal>
                  </ul>
                </Context>
              </li>
              <li>
                <a href="#">
                  <i class="context-menu-icon fas fa-fw fa-trash"></i>
                  This does nothing
                </a>
              </li>
            </ul>
          </Context>
          <a class="button" @click="$refs.modal2.show()">show modal</a>
          <Modal ref="modal2">
            <h2 class="box-title">An example modal</h2>
            <p>
              Mauris dignissim massa ac justo consequat porttitor. Lorem ipsum
              dolor sit amet, consectetur adipiscing elit. Mauris vel tellus
              suscipit, gravida libero a, egestas urna. Quisque tellus nisi,
              consequat et interdum non, posuere sed lacus. Morbi fermentum
              lorem sed vestibulum tristique. Vivamus scelerisque molestie
              ligula vel elementum. Etiam metus lacus, commodo sit amet
              tristique luctus, pulvinar eget justo. Fusce sed vehicula dolor.
              Aliquam sollicitudin fringilla augue, posuere maximus orci
              sollicitudin a. Vestibulum egestas tristique nunc, tristique
              dignissim mauris dictum imperdiet. Mauris ultrices ac eros at
              fringilla. Praesent ut tincidunt dui.
            </p>
          </Modal>
          <a
            class="button button-success"
            @click="
              $store.dispatch('notification/success', {
                title: 'Custom success notification',
                message: 'Mauris dignissim massa ac justo consequat porttitor.'
              })
            "
            >toggle success notification</a
          >
          <a
            class="button button-error"
            @click="
              $store.dispatch('notification/error', {
                title: 'Custom error notification',
                message: 'Mauris dignissim massa ac justo consequat porttitor.'
              })
            "
            >toggle error notification</a
          >
          <a
            class="button button-warning"
            @click="
              $store.dispatch('notification/warning', {
                title: 'Custom warning notification',
                message: 'Mauris dignissim massa ac justo consequat porttitor.'
              })
            "
            >toggle warning notification</a
          >
          <a
            class="button"
            @click="
              $store.dispatch('notification/info', {
                title: 'Custom info notification',
                message: 'Mauris dignissim massa ac justo consequat porttitor.'
              })
            "
            >toggle info notification</a
          >
        </div>
        <div class="margin-bottom-3">
          <div class="modal-box">
            <a class="modal-close">
              <i class="fas fa-times"></i>
            </a>
            <h2 class="box-title">An example modal</h2>
            <p>
              Mauris dignissim massa ac justo consequat porttitor. Lorem ipsum
              dolor sit amet, consectetur adipiscing elit. Mauris vel tellus
              suscipit, gravida libero a, egestas urna. Quisque tellus nisi,
              consequat et interdum non, posuere sed lacus. Morbi fermentum
              lorem sed vestibulum tristique. Vivamus scelerisque molestie
              ligula vel elementum. Etiam metus lacus, commodo sit amet
              tristique luctus, pulvinar eget justo. Fusce sed vehicula dolor.
              Aliquam sollicitudin fringilla augue, posuere maximus orci
              sollicitudin a. Vestibulum egestas tristique nunc, tristique
              dignissim mauris dictum imperdiet. Mauris ultrices ac eros at
              fringilla. Praesent ut tincidunt dui.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Notifications from '@baserow/modules/core/components/notifications/Notifications'

export default {
  components: {
    Notifications
  },
  head() {
    return {
      title: 'Style guide'
    }
  },
  data() {
    return {
      checkbox: false,
      dropdown: null
    }
  }
}
</script>
