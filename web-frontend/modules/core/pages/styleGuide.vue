<template>
  <div>
    <Toasts></Toasts>
    <div class="style-guide__wrapper">
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
          <FormInput
            v-model="input"
            label="Small text field"
            value="This is the value"
          />
          <FormInput
            v-model="input"
            label="Small text field with error"
            error="Please do something different"
          />
          <FormInput
            v-model="input"
            label="Small text field with placeholder"
            placeholder="Enter something here"
          />
          <FormInput
            v-model="input"
            label="Small text field disabled"
            placeholder="Enter something here"
            disabled
          />
          <FormInput
            v-model="input"
            label="Small text field loading"
            placeholder="Enter something here"
            loading
          />
          <FormInput
            v-model="input"
            label="Icon text field"
            placeholder="Enter something here"
            icon-right="clock"
          />
          <FormInput
            v-model="input"
            label="Icon text field with error"
            placeholder="Enter something here"
            icon-right="clock"
            error="This field is mandatory"
          />
          <FormInput
            v-model="input"
            label="Icon text field left"
            placeholder="Enter something here"
            icon-left="search"
          />
          <FormInput
            v-model="input"
            label="Icon text field right loading"
            placeholder="Enter something here"
            icon-right="search"
            loading
          />
          <FormInput
            v-model="input"
            label="Icon text field left loading"
            placeholder="Enter something here"
            icon-left="search"
            loading
          />
          <FormInput
            v-model="input"
            label="Large text field"
            placeholder="Enter something here"
            large
          />
          <FormInput
            v-model="input"
            label="Large password field"
            placeholder="Enter something here"
            type="password"
            large
          />
          <FormInput
            v-model="input"
            label="Large icon field"
            placeholder="Enter something here"
            large
            icon-right="clock"
          />
          <FormInput
            v-model="input"
            label="Large icon field left"
            placeholder="Enter something here"
            large
            icon-left="search"
          />
          <FormInput
            v-model="input"
            horizontal
            label="Horizontal Large icon field left"
            placeholder="Enter something here"
            large
            icon-left="search"
          />
          <div class="control">
            <label class="control__label">Checkbox field</label>
            <div class="control__elements">
              value: {{ checkbox }}
              <br />
              <br />
              <Checkbox v-model="checkbox"></Checkbox>
              <Checkbox v-model="checkbox">With text</Checkbox>
            </div>
          </div>
          <div class="control">
            <label class="control__label">Radio field</label>
            <div class="control__elements">
              value: {{ radio }}
              <br />
              <br />
              <Radio v-model="radio" value=""></Radio>
              <Radio v-model="radio" value="a">Option A</Radio>
              <Radio v-model="radio" value="b">Option B</Radio>
              <Radio v-model="radio" value="c">Option C</Radio>
              <Radio v-model="radio" value="d" :disabled="true">Option D</Radio>
              <Radio v-model="radio" value="e" :loading="true">Option E</Radio>
            </div>
          </div>
          <div class="control">
            <label class="control__label">Radio buttons</label>
            <div
              class="control__elements"
              :style="{ backgroundColor: 'white', padding: '5px' }"
            >
              value: {{ radioButton }}
              <br />
              <br />
              <RadioButton v-model="radioButton" value="">None</RadioButton>
              <RadioButton v-model="radioButton" value="a"
                >Option A</RadioButton
              >
              <RadioButton v-model="radioButton" value="b"
                >Option B</RadioButton
              >
              <RadioButton v-model="radioButton" value="c"
                >Option C</RadioButton
              >

              <RadioButton v-model="radioButton" value="g" :disabled="true">
                Option D
              </RadioButton>
              <RadioButton v-model="radioButton" value="h" :loading="true">
                Option E
              </RadioButton>
            </div>
            <div
              class="control__elements"
              :style="{ backgroundColor: 'white', padding: '5px' }"
            >
              <RadioButton
                v-model="radioButton"
                value="d"
                icon="align-left"
              ></RadioButton>
              <RadioButton
                v-model="radioButton"
                value="e"
                icon="align-center"
              ></RadioButton>
              <RadioButton
                v-model="radioButton"
                value="f"
                icon="align-right"
              ></RadioButton>
            </div>
            <div
              class="control__elements"
              :style="{ backgroundColor: 'white', padding: '5px' }"
            >
              <RadioButton
                v-model="radioButton"
                value="d"
                icon="align-left"
                size="large"
              ></RadioButton>
              <RadioButton
                v-model="radioButton"
                value="e"
                icon="align-center"
                size="large"
              ></RadioButton>
              <RadioButton
                v-model="radioButton"
                value="f"
                icon="align-right"
                size="large"
              ></RadioButton>
            </div>
          </div>
          <div class="control">
            <label class="control__label">Switch field</label>
            <div class="control__elements">
              value: {{ switchValue }}
              <br />
              <br />
              <SwitchInput v-model="switchValue"></SwitchInput>
              <SwitchInput v-model="switchValue">With text</SwitchInput>
              <SwitchInput v-model="switchUnknown">With text</SwitchInput>
              <SwitchInput v-model="switchValue" :large="true"></SwitchInput>
              <SwitchInput v-model="switchValue" :large="true">
                With text
              </SwitchInput>
              <SwitchInput v-model="switchUnknown" :large="true">
                With text
              </SwitchInput>
            </div>
          </div>
          <div class="control">
            <label class="control__label">Dropdown</label>
            <div class="control__elements">
              value: {{ dropdown }}
              <br />
              <br />
              <div style="width: 200px">
                <Dropdown v-model="dropdown">
                  <DropdownItem name="Choice 1" value="choice-1"></DropdownItem>
                  <DropdownItem
                    name="Choice 2"
                    value="choice-2"
                    icon="edit"
                    description="Lorem ipsum dolor sit amet, consectetur."
                  ></DropdownItem>
                  <DropdownItem
                    name="Choice 3"
                    value="choice-3"
                    icon="database"
                  ></DropdownItem>
                  <DropdownItem
                    name="Choice 4"
                    value="choice-4"
                    icon="times"
                    :disabled="true"
                  ></DropdownItem>
                  <DropdownItem
                    name="Choice 5"
                    value="choice-5"
                    icon="edit"
                    description="Lorem ipsum dolor sit amet, consectetur."
                  ></DropdownItem>
                  <DropdownItem
                    name="Choice 6"
                    value="choice-6"
                    icon="edit"
                    description="Lorem ipsum dolor sit amet, consectetur."
                  ></DropdownItem>
                </Dropdown>
              </div>
            </div>
          </div>
          <div class="control">
            <label class="control__label">Dropdown</label>
            <div class="control__elements">
              value: {{ dropdown }}
              <br />
              <br />
              <div style="width: 200px">
                <Dropdown v-model="dropdown" :show-search="false">
                  <DropdownItem name="Choice 1" value="choice-1"></DropdownItem>
                  <DropdownItem
                    name="Choice 2"
                    value="choice-2"
                    icon="edit"
                  ></DropdownItem>
                  <DropdownItem
                    name="Choice 3"
                    value="choice-3"
                    icon="database"
                  ></DropdownItem>
                  <DropdownItem
                    name="Choice 4"
                    value="choice-4"
                    icon="times"
                    :disabled="true"
                  ></DropdownItem>
                </Dropdown>
              </div>
            </div>
          </div>
          <div class="control">
            <label class="control__label">Very long dropdown</label>
            <div class="control__elements">
              <div style="width: 200px">
                <Dropdown v-model="longDropdown">
                  <DropdownItem
                    :key="'some-2'"
                    :name="'Something'"
                    :value="'some-2'"
                  ></DropdownItem>
                  <DropdownItem
                    :key="'test-3'"
                    :name="'Test 3'"
                    :value="'test3'"
                  ></DropdownItem>
                  <DropdownItem
                    v-for="i in [
                      0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
                    ]"
                    :key="i"
                    :name="'Choice ' + i"
                    :value="i"
                    :disabled="i === 7"
                  ></DropdownItem>
                  <DropdownItem
                    :key="'test-1'"
                    :name="'Test 1'"
                    :value="'test1'"
                  ></DropdownItem>
                  <DropdownItem
                    :key="'test-2'"
                    :name="'Test 2'"
                    :value="'test2'"
                  ></DropdownItem>
                </Dropdown>
              </div>
            </div>
          </div>
          <div class="control">
            <label class="control__label">Dropdown with footer</label>
            <div class="control__elements">
              value: {{ dropdown }}
              <br />
              <br />
              <div style="width: 200px">
                <Dropdown v-model="dropdown" show-search show-footer>
                  <DropdownItem name="Choice 1" value="choice-1"></DropdownItem>
                  <DropdownItem
                    name="Choice 2"
                    value="choice-2"
                    icon="edit"
                  ></DropdownItem>
                  <DropdownItem
                    name="Choice 3"
                    value="choice-3"
                    icon="database"
                  ></DropdownItem>
                  <DropdownItem
                    name="Choice 4"
                    value="choice-4"
                    icon="times"
                    :disabled="true"
                  ></DropdownItem>
                  <template #footer>
                    <a
                      class="select__footer-button"
                      @click="$refs.IntegrationCreateEditModal.show()"
                    >
                      <i class="fas fa-plus"></i>
                      Add item
                    </a>
                  </template>
                </Dropdown>
              </div>
            </div>
          </div>
          <div class="control">
            <label class="control__label">
              Dropdown by link {{ dropdown }}
            </label>
            <div class="control__elements">
              <div style="width: 200px">
                <a
                  ref="dropdownLink"
                  @click="$refs.dropdown1.toggle($refs.dropdownLink)"
                  >Open dropdown</a
                >
                <Dropdown
                  ref="dropdown1"
                  v-model="dropdown"
                  :show-input="false"
                >
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
                  <DropdownItem
                    name="Choice 4"
                    value="choice-4"
                    icon="times"
                    :disabled="true"
                  ></DropdownItem>
                </Dropdown>
              </div>
            </div>
          </div>
          <div class="control">
            <label class="control__label">Datepicker field</label>
            <div class="control__elements">
              value: {{ date }}
              <br />
              <br />
              <client-only>
                <date-picker
                  v-model="date"
                  :inline="true"
                  :monday-first="true"
                  class="datepicker"
                ></date-picker>
              </client-only>
            </div>
          </div>
        </div>
        <div class="margin-bottom-3">
          <Alert title="Toast message" icon="exclamation">
            Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
            elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui ligula.
            Pellentesque feugiat erat vel porttitor euismod. Duis nec viverra
            urna. Praesent.
          </Alert>
          <Alert title="Toast message">
            Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
            elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui ligula.
            Pellentesque feugiat erat vel porttitor euismod. Duis nec viverra
            urna. Praesent lobortis feugiat erat, nec volutpat nulla tincidunt
            vel. In hac habitasse platea dictumst. Aenean fringilla lacus nunc,
            non pharetra mauris pulvinar lacinia. Aenean ut sem lacinia,
            sagittis quam sed, pellentesque orci. Aenean non consequat mi. Nunc
            laoreet ligula a nunc eleifend, nec accumsan felis euismod.
          </Alert>
          <Alert title="Toast message" type="success" icon="exclamation">
            Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
            elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui ligula.
            Pellentesque feugiat erat vel porttitor euismod. Duis nec viverra
            urna. Praesent.
          </Alert>
          <Alert title="Toast message" type="warning" icon="exclamation">
            Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
            elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui ligula.
            Pellentesque feugiat erat vel porttitor euismod. Duis nec viverra
            urna. Praesent.
          </Alert>
          <Alert title="Toast message" type="error" icon="exclamation">
            Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
            elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui ligula.
            Pellentesque feugiat erat vel porttitor euismod. Duis nec viverra
            urna. Praesent.
          </Alert>
          <Alert title="Toast message" simple icon="exclamation">
            Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
            elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui ligula.
            Pellentesque feugiat erat vel porttitor euismod. Duis nec viverra
            urna. Praesent.
          </Alert>
          <Alert title="Toast message" simple>
            Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
            elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui ligula.
            Pellentesque feugiat erat vel porttitor euismod. Duis nec viverra
            urna. Praesent.
          </Alert>
          <Alert title="Toast message" type="success" simple icon="exclamation">
            Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
            elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui ligula.
            Pellentesque feugiat erat vel porttitor euismod. Duis nec viverra
            urna. Praesent.
          </Alert>
          <Alert
            title="Toast message"
            type="warning"
            simple
            shadow
            icon="exclamation"
          >
            Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
            elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui ligula.
            Pellentesque feugiat erat vel porttitor euismod. Duis nec viverra
            urna. Praesent.
          </Alert>
          <Alert
            title="Toast message"
            type="error"
            simple
            shadow
            icon="exclamation"
          >
            Lorem ipsum dolor sit amet, <a href="#">consectetur</a> adipiscing
            elit. Sed quis gravida ante. Nulla nec elit dui. Nam nec dui ligula.
            Pellentesque feugiat erat vel porttitor euismod. Duis nec viverra
            urna. Praesent.
          </Alert>
        </div>
        <div
          class="margin-bottom-3 style-guide__buttons"
          :style="{ backgroundColor: 'white', padding: '5px' }"
        >
          <h3>Tiny size</h3>
          <Button size="tiny">button</Button>
          <Button size="tiny" disabled>button[disabled]</Button>
          <Button size="tiny" type="primary">button.button-success</Button>
          <Button size="tiny" type="success">button.button-success</Button>
          <Button size="tiny" type="warning">button.button-warning</Button>
          <Button size="tiny" type="error">button.button-error</Button>
          <Button size="tiny" append-icon="lock-open">button</Button>
          <Button size="tiny" type="link" prepend-icon="arrow-left">
            button
          </Button>
          <Button size="tiny" type="ghost">button.button-ghost</Button>
          <Button size="tiny" type="link">button.button-link</Button>
          <Button size="tiny" icon="user-check"></Button>
          <Button size="tiny" icon="user-check" type="ghost"></Button>
          <Button size="tiny" icon="user-check" type="link"></Button>
        </div>
        <div
          class="margin-bottom-3 style-guide__buttons"
          :style="{ backgroundColor: 'white', padding: '5px' }"
        >
          <h3>Normal link</h3>
          <Button tag="a" href="#">a.button</Button>
          <Button tag="a" disabled href="#">a.button[disabled]</Button>
          <Button tag="a" type="success" href="#">
            a.button.button-success
          </Button>
          <Button tag="a" type="warning">a.button.button-warning</Button>
          <Button tag="a" type="error">a.button.button-error</Button>
          <Button tag="a" append-icon="lock-open">a.button</Button>
          <Button tag="a" type="link" prepend-icon="arrow-left"
            >a.button</Button
          >
          <Button tag="a" type="ghost">a.button.button-ghost</Button>
          <Button tag="a" type="link">a.button.button-link</Button>
          <Button tag="a" icon="user-check"></Button>
          <Button tag="a" icon="user-check" type="ghost"></Button>
          <Button tag="a" icon="user-check" type="link"></Button>
        </div>
        <div
          class="margin-bottom-3 style-guide__buttons"
          :style="{ backgroundColor: 'white', padding: '5px' }"
        >
          <h3>Normal button</h3>
          <Button>button.button</Button>
          <Button disabled>button[disabled]</Button>
          <Button type="success">button.button-success</Button>
          <Button type="warning">button.button-warning</Button>
          <Button type="error">button.button-error</Button>
          <Button append-icon="lock-open">button</Button>
          <Button type="link" prepend-icon="arrow-left">button</Button>
          <Button type="ghost">button.button-ghost</Button>
          <Button type="link">button.button-link</Button>
          <Button icon="user-check"></Button>
          <Button icon="user-check" type="ghost"></Button>
          <Button type="light">button.light</Button>
          <Button type="light" active>button.light.active</Button>
          <Button type="light" icon="trash"></Button>
          <Button type="link" icon="trash"></Button>
        </div>
        <div
          class="margin-bottom-3 style-guide__buttons"
          :style="{ backgroundColor: 'white', padding: '5px' }"
        >
          <h3>Large size</h3>
          <Button size="large">button</Button>
          <Button size="large" disabled>button[disabled]</Button>
          <Button type="plain" size="large">button-plain</Button>
          <Button size="large" type="success">button.button-success</Button>
          <Button size="large" type="warning">button.button-warning</Button>
          <Button size="large" type="error">button.button-error</Button>
          <Button size="large" append-icon="lock-open">button</Button>
          <Button size="large" prepend-icon="arrow-left">button</Button>
          <Button size="large" type="ghost">button.button-ghost</Button>
          <Button size="large" type="link">button.button-link</Button>
          <Button size="large" icon="user-check"></Button>
          <Button size="large" icon="user-check" type="ghost"></Button>
          <Button size="large" icon="user-check" type="link"></Button>
        </div>
        <div
          class="margin-bottom-3"
          :style="{ backgroundColor: 'white', padding: '5px' }"
        >
          <h3>Loading</h3>
          <Button size="tiny" loading>Loading</Button>
          <Button loading>Loading</Button>
          <Button append-icon="search" loading>Loading</Button>
          <Button type="link" loading>Loading</Button>
          <Button size="large" loading>Loading</Button>
          <Button size="large" type="ghost" loading>Loading</Button>
          <Button size="large" icon="user-check" loading></Button>
          <Button type="light" loading>button.light.loading</Button>
          <Button type="link" loading>button.link.loading</Button>
          <Button type="light" active loading>
            button.light.active.loading
          </Button>
          <Button type="link" icon="trash" loading />
        </div>
        <div
          class="margin-bottom-3"
          style="background-color: #ffffff; padding: 20px"
        >
          <h3>Classic tabs</h3>
          <Tabs>
            <Tab :selected="true" :title="'Tab 1'">
              <p>
                Tab 1 content Lorem ipsum dolor sit amet,
                <a href="#">consectetur</a> adipiscing elit. Sed quis gravida
                ante. Nulla nec elit dui. Nam nec dui ligula. Pellentesque
                feugiat erat vel porttitor euismod. Duis nec viverra urna.
                Praesent.
              </p>
            </Tab>
            <Tab :title="'Tab 2'">
              <p>
                Tab 2 content Lorem ipsum dolor sit amet,
                <a href="#">consectetur</a> adipiscing elit. Sed quis gravida
                ante. Nulla nec elit dui. Nam nec dui ligula. Pellentesque
                feugiat erat vel porttitor euismod. Duis nec viverra urna.
                Praesent.
              </p>
            </Tab>
            <Tab :title="'Tab 3'">
              <p>
                Tab 3 content Lorem ipsum dolor sit amet,
                <a href="#">consectetur</a> adipiscing elit. Sed quis gravida
                ante. Nulla nec elit dui. Nam nec dui ligula. Pellentesque
                feugiat erat vel porttitor euismod. Duis nec viverra urna.
                Praesent.
              </p>
            </Tab>
          </Tabs>
        </div>
        <div
          class="margin-bottom-3"
          style="background-color: #ffffff; padding: 20px"
        >
          <h3>No separation</h3>
          <Tabs no-separation>
            <Tab :selected="true" :title="'Tab 1'">
              <p>
                Tab 1 content Lorem ipsum dolor sit amet,
                <a href="#">consectetur</a> adipiscing elit. Sed quis gravida
                ante. Nulla nec elit dui. Nam nec dui ligula. Pellentesque
                feugiat erat vel porttitor euismod. Duis nec viverra urna.
                Praesent.
              </p>
            </Tab>
            <Tab :title="'Tab 2'">
              <p>
                Tab 2 content Lorem ipsum dolor sit amet,
                <a href="#">consectetur</a> adipiscing elit. Sed quis gravida
                ante. Nulla nec elit dui. Nam nec dui ligula. Pellentesque
                feugiat erat vel porttitor euismod. Duis nec viverra urna.
                Praesent.
              </p>
            </Tab>
            <Tab :title="'Tab 3'">
              <p>
                Tab 3 content Lorem ipsum dolor sit amet,
                <a href="#">consectetur</a> adipiscing elit. Sed quis gravida
                ante. Nulla nec elit dui. Nam nec dui ligula. Pellentesque
                feugiat erat vel porttitor euismod. Duis nec viverra urna.
                Praesent.
              </p>
            </Tab>
          </Tabs>
        </div>

        <div class="margin-bottom-3">
          <div class="tooltip margin-bottom-2">
            <div class="tooltip__content">Example tooltip</div>
          </div>
          <div class="tooltip tooltip--top">
            <div class="tooltip__content">Tooltip top</div>
          </div>
        </div>
        <div class="margin-bottom-3 style-guide__contexts">
          <div class="context">
            <div class="context__menu-title">Vehicles</div>
            <ul class="context__menu">
              <li>
                <a href="#">
                  <i class="context__menu-icon fas fa-fw fa-pen"></i>
                  Rename database
                </a>
              </li>
              <li>
                <a href="#">
                  <i class="context__menu-icon fas fa-fw fa-trash"></i>
                  Delete table
                </a>
              </li>
              <li>
                <a href="#" class="context__menu-item--loading">
                  <i class="context__menu-icon fas fa-fw fa-trash"></i>
                  Loading
                </a>
              </li>
            </ul>
          </div>
          <div class="context" style="max-width: 264px">
            <div class="context__menu-title">Workspace permissions</div>
            <ul class="context__menu context__menu--can-be-active">
              <li>
                <a href="#" class="active">
                  Admin
                  <div class="context__menu-item-description">
                    Description of what an admin can or can’t do on the
                    workspace.
                  </div>
                </a>
              </li>
              <li>
                <a href="#" class="context__menu-item--loading">
                  Builder
                  <div class="context__menu-item-description">
                    Description of what a builder can or can’t do on the
                    workspace.
                  </div>
                </a>
              </li>
              <li>
                <a class="color-error" href="#"> Remove from workspace </a>
              </li>
            </ul>
          </div>
          <div class="select">
            <div class="select__search">
              <i class="select__search-icon fas fa-search"></i>
              <input
                type="text"
                class="select__search-input"
                placeholder="Search views"
              />
            </div>
            <ul v-auto-overflow-scroll class="select__items">
              <li class="select__item active">
                <a href="#" class="select__item-link">
                  <div class="select__item-name">Workspace name 1</div>
                </a>
                <a href="#" class="select__item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
              <li class="select__item">
                <a href="#" class="select__item-link">
                  <div class="select__item-name">Workspace name 2</div>
                </a>
                <a href="#" class="select__item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
              <li class="select__item select__item--loading">
                <a href="#" class="select__item-link">
                  <div class="select__item-name">Workspace name 3</div>
                </a>
                <a href="#" class="select__item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
              <li class="select__item">
                <a href="#" class="select__item-link">
                  <div class="select__item-name">roup name 4</div>
                </a>
                <a href="#" class="select__item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
            </ul>
            <div class="select__footer">
              <a href="#" class="select__footer-button">
                <i class="fas fa-plus"></i>
                Do something
              </a>
            </div>
          </div>
        </div>
        <div class="margin-bottom-3 style-guide__contexts">
          <div class="select">
            <div class="select__search">
              <i class="select__search-icon fas fa-search"></i>
              <input
                type="text"
                class="select__search-input"
                placeholder="Search views"
              />
            </div>
            <ul v-auto-overflow-scroll class="select__items">
              <li class="select__item">
                <a href="#" class="select__item-link">
                  <div class="select__item-name">
                    <i
                      class="select__item-icon fas fa-th fa-fw color-primary"
                    ></i>
                    Grid view name
                  </div>
                </a>
                <a
                  href="#"
                  class="select__item-options"
                  data-context=".context"
                >
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
              <li class="select__item">
                <a href="#" class="select__item-link">
                  <div class="select__item-name">
                    <i
                      class="select__item-icon fas fa-th fa-fw color-primary"
                    ></i>
                    Grid view option 2.
                  </div>
                </a>
                <a href="#" class="select__item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
              <li class="select__item">
                <a href="#" class="select__item-link">
                  <div class="select__item-name">
                    <i
                      class="select__item-icon fas fa-th fa-fw color-primary"
                    ></i>
                    Grid view 2
                  </div>
                </a>
                <a href="#" class="select__item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
              <li class="select__item">
                <a href="#" class="select__item-link">
                  <div class="select__item-name">
                    <i
                      class="select__item-icon fas fa-th fa-fw color-primary"
                    ></i>
                    Grid view 3
                  </div>
                </a>
                <a href="#" class="select__item-options">
                  <i class="fas fa-ellipsis-v"></i>
                </a>
              </li>
            </ul>
            <div class="select__footer">
              <div class="select__footer-create">
                <a class="select__footer-create-link"
                  ><i class="select__footer-create-icon fas fa-bars"></i>
                  Grid </a
                ><a class="select__footer-create-link"
                  ><i class="select__footer-create-icon fas fa-th-large"></i>
                  Gallery </a
                ><a class="select__footer-create-link"
                  ><i class="select__footer-create-icon fas fa-edit"></i>
                  Form </a
                ><a class="select__footer-create-link"
                  ><i class="select__footer-create-icon fas fa-trello fab"></i>
                  Kanban
                </a>
              </div>
            </div>
          </div>
          <div class="context datepicker-context">
            <client-only>
              <date-picker
                v-model="date"
                :inline="true"
                :monday-first="true"
                class="datepicker"
              ></date-picker>
            </client-only>
          </div>
          <div class="time-select">
            <ul>
              <li>
                <a href="#">00:00</a>
              </li>
              <li>
                <a href="#">00:30</a>
              </li>
              <li>
                <a href="#" class="active">01:00</a>
              </li>
              <li>
                <a href="#">01:30</a>
              </li>
              <li>
                <a href="#">02:00</a>
              </li>
              <li>
                <a href="#">02:30</a>
              </li>
              <li>
                <a href="#">03:00</a>
              </li>
              <li>
                <a href="#">03:30</a>
              </li>
            </ul>
          </div>
        </div>
        <div class="formula-field margin-bottom-3">
          <div class="formula-field__input">
            <AutoExpandableTextarea
              v-model="formula"
              class="formula-field__input-formula"
            ></AutoExpandableTextarea>
          </div>
          <div class="formula-field__body">
            <div class="formula-field__items">
              <ul class="formula-field__item-group">
                <li class="formula-field__item-group-title">Fields</li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-font formula-field__item-icon" />
                    Text
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-hashtag formula-field__item-icon" />
                    Number
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-check-square formula-field__item-icon" />
                    Checkbox
                  </a>
                </li>
              </ul>
              <ul class="formula-field__item-group">
                <li class="formula-field__item-group-title">Constants</li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-hashtag formula-field__item-icon" />
                    e
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-hashtag formula-field__item-icon" />
                    pi
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-check-square formula-field__item-icon" />
                    true
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-check-square formula-field__item-icon" />
                    false
                  </a>
                </li>
              </ul>
              <ul class="formula-field__item-group">
                <li class="formula-field__item-group-title">Operators</li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-font formula-field__item-icon" />
                    If
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-hashtag formula-field__item-icon" />
                    add
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-hashtag formula-field__item-icon" />
                    subtract
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-hashtag formula-field__item-icon" />
                    multiply
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-hashtag formula-field__item-icon" />
                    divide
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-hashtag formula-field__item-icon" />
                    pow
                  </a>
                </li>
              </ul>
              <ul class="formula-field__item-group">
                <li class="formula-field__item-group-title">Functions</li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-font formula-field__item-icon" />
                    concat
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-font formula-field__item-icon" />
                    join
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-font formula-field__item-icon" />
                    slice
                  </a>
                </li>
                <li class="formula-field__item">
                  <a href="#" class="formula-field__item-link">
                    <i class="fas fa-hashtag formula-field__item-icon" />
                    length
                  </a>
                </li>
              </ul>
            </div>
            <div class="formula-field__description">
              <div class="formula-field__description-heading-1">concat</div>
              <div class="formula-field__description-text">
                Concatenates its arguments and returns the result.
              </div>
              <div class="formula-field__description-heading-2">Syntax</div>
              <pre
                class="formula-field__description-example"
              ><code>concat(text...)</code></pre>
              <div class="formula-field__description-heading-2">Examples</div>
              <pre
                class="formula-field__description-example"
              ><code>concat(“Hello”, “World”) == “HelloWorld”
“Hello” + “World” == “HelloWorld”</code></pre>
            </div>
          </div>
        </div>
        <div class="margin-bottom-3">
          <Button
            append-icon="pencil"
            @click="$refs.context1.toggle($event.target)"
          >
            Toggle context
          </Button>
          <Context ref="context1">
            <div class="context__menu-title">Vehicles</div>
            <ul class="context__menu">
              <li>
                <a href="#">
                  <i class="context__menu-icon fas fa-fw fa-pen"></i>
                  This does nothing
                </a>
              </li>
              <li>
                <a @click="$refs.context2.toggle($event.target)">
                  Open another context
                </a>
                <Context ref="context2">
                  <div class="context__menu-title">Open modal</div>
                  <ul class="context__menu">
                    <li>
                      <a @click="$refs.modal1.show()">
                        <i class="context__menu-icon fas fa-fw fa-pen"></i>
                        Click to open modal
                      </a>
                    </li>
                    <Modal ref="modal1">
                      <h2 class="box__title">Modal inside a context</h2>
                      <Button
                        icon="pencil"
                        @click="$refs.context3.toggle($event.target)"
                        >Toggle context</Button
                      >
                      <Context ref="context3">
                        <div class="context__menu-title">Vehicles</div>
                        <ul class="context__menu">
                          <li>
                            <a href="#">
                              <i
                                class="context__menu-icon fas fa-fw fa-pen"
                              ></i>
                              This does nothing
                            </a>
                          </li>
                          <li>
                            <a @click="$refs.context4.toggle($event.target)">
                              Open another context
                            </a>
                            <Context ref="context4">
                              <div class="context__menu-title">End!</div>
                            </Context>
                          </li>
                          <li>
                            <a href="#">
                              <i
                                class="context__menu-icon fas fa-fw fa-trash"
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
                  <i class="context__menu-icon fas fa-fw fa-trash"></i>
                  This does nothing
                </a>
              </li>
            </ul>
          </Context>
          <Button @click="$refs.modal2.show()">show modal</Button>
          <Modal ref="modal2">
            <h2 class="box__title">An example modal</h2>
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
          <Button
            type="success"
            @click="
              $store.dispatch('toast/success', {
                title: 'Custom success toast',
                message: 'Mauris dignissim massa ac justo consequat porttitor.',
              })
            "
          >
            toggle success toast
          </Button>
          <Button
            type="error"
            @click="
              $store.dispatch('toast/error', {
                title: 'Custom error toast',
                message: 'Mauris dignissim massa ac justo consequat porttitor.',
              })
            "
          >
            toggle error toast
          </Button>
          <Button
            type="warning"
            @click="
              $store.dispatch('toast/warning', {
                title: 'Custom warning toast',
                message: 'Mauris dignissim massa ac justo consequat porttitor.',
              })
            "
          >
            toggle warning toast
          </Button>
          <Button
            @click="
              $store.dispatch('toast/info', {
                title: 'Custom info toast',
                message: 'Mauris dignissim massa ac justo consequat porttitor.',
              })
            "
          >
            toggle info toast
          </Button>
        </div>
        <div class="margin-bottom-3">
          <div class="modal__box">
            <a class="modal__close">
              <i class="fas fa-times"></i>
            </a>
            <h2 class="box__title">An example modal</h2>
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
            <div class="delete-section">
              <div class="delete-section__label">
                <div class="delete-section__label-icon">
                  <i class="fas fa-exclamation"></i>
                </div>
                Will also be permanently deleted
              </div>
              <p class="delete-section__description">
                Mauris dignissim massa ac justo consequat porttitor. Lorem ipsum
                dolor sit amet, consectetur adipiscing elit. Mauris vel tellus
                suscipit, gravida libero a, egestas urna. Quisque tellus nisi,
                consequat et interdum non, posuere sed lacus.
              </p>
              <ul class="delete-section__list">
                <li>
                  <i class="delete-section__list-icon fas fa-database"></i>
                  Vehicles
                  <small>including 12 tables</small>
                </li>
                <li>
                  <i class="delete-section__list-icon fas fa-database"></i>
                  Webshop
                  <small>including 12 tables</small>
                </li>
              </ul>
            </div>
            <div class="actions actions--right">
              <Button size="large" overflow>Validate</Button>
            </div>
          </div>
          <div class="modal__box modal__box--with-sidebar">
            <a class="modal__close">
              <i class="fas fa-times"></i>
            </a>
            <div
              class="modal__box-sidebar modal__box-sidebar--left modal__box-sidebar--scrollable"
            >
              <div class="modal-sidebar__head">
                <div class="modal-sidebar__head-initials-icon">B</div>
                <div class="modal-sidebar__head-name">Settings</div>
              </div>
              <ul class="modal-sidebar__nav">
                <li>
                  <a class="modal-sidebar__nav-link active"
                    ><i class="fas modal-sidebar__nav-icon fa-user"></i>
                    Account
                  </a>
                </li>
                <li>
                  <a class="modal-sidebar__nav-link"
                    ><i class="fas modal-sidebar__nav-icon fa-lock"></i>
                    Password
                  </a>
                </li>
                <li>
                  <a class="modal-sidebar__nav-link"
                    ><i class="fas modal-sidebar__nav-icon fa-key"></i>
                    API Tokens
                  </a>
                </li>
                <li>
                  <a class="modal-sidebar__nav-link"
                    ><i class="fas modal-sidebar__nav-icon fa-user-slash"></i>
                    Delete account
                  </a>
                </li>
              </ul>
            </div>
            <div class="modal__box-content">
              <h2 class="box__title">An example modal</h2>
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
        <div class="margin-bottom-3">
          <div class="card" style="width: 320px">
            <div class="card__cover">
              <div
                v-if="false"
                class="card__cover-image"
                :style="{
                  'background-image':
                    'url(https://www.w3schools.com/cssref/mountain.jpg)',
                }"
              ></div>
            </div>
            <div class="card__fields">
              <div class="card__field">
                <div class="card__field-name">Text</div>
                <div class="card__field-value">
                  <div class="card-text">This is a single line text field</div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">Long text</div>
                <div class="card__field-value">
                  <div class="card-text">
                    This is a long text field with a very long content that
                    doesn't fit.
                  </div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">Link row</div>
                <div class="card__field-value">
                  <div class="card-many-to-many__list-wrapper">
                    <div class="card-many-to-many__list">
                      <div class="card-many-to-many__item card-link-row">
                        <span class="card-many-to-many__name">
                          Value 1 with a very long name that doesn't
                        </span>
                      </div>
                      <div
                        class="card-many-to-many__item card-link-row card-link-row--unnamed"
                      >
                        <span class="card-many-to-many__name">
                          unnamed row 1
                        </span>
                      </div>
                      <div class="card-many-to-many__item card-link-row">
                        <span class="card-many-to-many__name">
                          Another value
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">Number</div>
                <div class="card__field-value">
                  <div class="card-text">205</div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">Decimal</div>
                <div class="card__field-value">
                  <div class="card-text">205.55</div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">Boolean</div>
                <div class="card__field-value">
                  <div class="card-boolean">
                    <i class="fas fa-check"></i>
                  </div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">Date</div>
                <div class="card__field-value">
                  <div class="card-text">2021-01-01</div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">Datetime</div>
                <div class="card__field-value">
                  <div class="card-text">2021-01-01</div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">URL</div>
                <div class="card__field-value">
                  <div class="card-text">
                    <a href="#">http://baserow.io</a>
                  </div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">Email</div>
                <div class="card__field-value">
                  <div class="card-text">
                    <a href="#">bram@baserow.io</a>
                  </div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">File</div>
                <div class="card__field-value">
                  <div class="card-file__list-wrapper">
                    <ul class="card-file__list">
                      <li class="card-file__item">
                        <img
                          src="http://localhost:4000/media/thumbnails/tiny/NcTfu10MwH9xtUkzL5jcmqIDXE0vkHin_1e01581444c66c952aa585f6fc79a671885b75053d275329f20e7b5faa73d7ec.png"
                          class="card-file__image"
                        />
                      </li>
                      <li class="card-file__item">
                        <img
                          src="http://localhost:4000/media/thumbnails/tiny/E413HC1eHsw9gakeRrpUOodHprEBT1pv_01bb5d9bbbd9addb39d1352877ca061573f2ca8ba64631ae5d4b7f8e16f6b18b.png"
                          class="card-file__image"
                        />
                      </li>
                      <li class="card-file__item">
                        <i class="fas card-file__icon fa-file"></i>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">Single select</div>
                <div class="card__field-value">
                  <div
                    class="card-single-select-option background-color--orange"
                  >
                    Option 1 with a very long name that doesn't fit
                    unfortunately.
                  </div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">Single select</div>
                <div class="card__field-value">
                  <div class="card-single-select-option background-color--gray">
                    Option 2
                  </div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">Multiple select</div>
                <div class="card__field-value">
                  <div class="card-many-to-many__list-wrapper">
                    <div class="card-many-to-many__list">
                      <div
                        class="card-many-to-many__item card-multiple-select-option background-color--green"
                      >
                        <span class="card-many-to-many__name">
                          Option value 1
                        </span>
                      </div>
                      <div
                        class="card-many-to-many__item card-multiple-select-option background-color--blue"
                      >
                        <span class="card-many-to-many__name">
                          Option 2 with a very long name that doesn't fit
                        </span>
                      </div>
                      <div
                        class="card-many-to-many__item card-multiple-select-option background-color--blue"
                      >
                        <span class="card-many-to-many__name"> Option 3 </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card__field">
                <div class="card__field-name">Phone</div>
                <div class="card__field-value">
                  <div class="card-text">
                    <a href="#">+316 12345678</a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div
          class="margin-bottom-3"
          style="background-color: #ffffff; position: relative; height: 1000px"
        >
          <div class="data-table">
            <div class="data-table__header">
              <h1 class="data-table__title">12 Members in ACME Corp</h1>
              <div class="data-table__actions">
                <div class="input__with-icon input__with-icon--left">
                  <input
                    type="text"
                    placeholder="Find member..."
                    class="input input--large"
                  />
                  <i class="fas fa-search"></i>
                </div>
                <Button href="#" size="large" class="margin-left-2">
                  Invite member
                </Button>
              </div>
            </div>
            <div class="data-table__body">
              <table class="data-table__table">
                <thead>
                  <tr class="data-table__table-row">
                    <th
                      class="data-table__table-cell data-table__table-cell--sticky-left data-table__table-cell--header"
                    >
                      <div class="data-table__table-cell-head">
                        <Checkbox
                          v-model="checkbox"
                          class="checkbox--small"
                        ></Checkbox>
                      </div>
                    </th>
                    <th
                      class="data-table__table-cell data-table__table-cell--header"
                    >
                      <div class="data-table__table-cell-head">
                        <a href="#" class="data-table__table-cell-head-link"
                          >Name</a
                        >
                        <div>
                          <i class="fas fa-sort-down"></i>
                          0
                        </div>
                      </div>
                    </th>
                    <th
                      class="data-table__table-cell data-table__table-cell--header"
                    >
                      <div class="data-table__table-cell-head">Email</div>
                    </th>
                    <th
                      class="data-table__table-cell data-table__table-cell--header"
                    >
                      <div class="data-table__table-cell-head">
                        Workspace permissions
                        <div>
                          <i class="fas fa-sort-up"></i>
                          1
                        </div>
                      </div>
                    </th>
                    <th
                      class="data-table__table-cell data-table__table-cell--header"
                    >
                      <div class="data-table__table-cell-head">Team</div>
                    </th>
                    <th
                      class="data-table__table-cell data-table__table-cell--header data-table__table-cell--sticky-right"
                    >
                      <div class="data-table__table-cell-head"></div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(i, i2) in new Array(10)"
                    :key="i2"
                    class="data-table__table-row"
                    :class="{
                      'data-table__table-row--selected': i2 === 2,
                      'data-table__table-row--hover': i2 === 4,
                    }"
                  >
                    <td
                      class="data-table__table-cell data-table__table-cell--sticky-left"
                    >
                      <div class="data-table__table-cell-content">
                        <Checkbox
                          v-model="checkbox"
                          class="checkbox--small"
                        ></Checkbox>
                      </div>
                    </td>
                    <td class="data-table__table-cell">
                      <div class="data-table__table-cell-content">
                        This is a very long name that doesn't completely fit.
                      </div>
                    </td>
                    <td class="data-table__table-cell">
                      <div class="data-table__table-cell-content">
                        This is a very long name that doesn't completely fit.
                      </div>
                    </td>
                    <td class="data-table__table-cell">
                      <div class="data-table__table-cell-content">
                        This is a very long name that doesn't completely fit.
                      </div>
                    </td>
                    <td class="data-table__table-cell">
                      <div class="data-table__table-cell-content">
                        This is a very long name that doesn't completely fit.
                      </div>
                    </td>
                    <td
                      class="data-table__table-cell data-table__table-cell--sticky-right"
                    >
                      <div class="data-table__table-cell-content">
                        <div class="data-table__more-wrapper">
                          <a href="#" class="data-table__more">
                            <i class="fas fa-ellipsis-h"></i>
                          </a>
                        </div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="data-table__footer">
              <div class="paginator">
                <div class="paginator__name">page</div>
                <div class="paginator__group">
                  <a class="paginator__button paginator__button--disabled"
                    ><i class="fas fa-caret-left"></i
                  ></a>
                  <input
                    type="number"
                    class="input paginator__page-input"
                    value="1"
                  />
                  <div class="paginator__count">of 233</div>
                  <a class="paginator__button"
                    ><i class="fas fa-caret-right"></i
                  ></a>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="margin-bottom-3" style="background-color: #ffffff">
          <h2>List component</h2>
          <List
            :items="[
              { id: 1, name: 'test', image: image },
              { id: 2, name: 'test2', image: image },
              { id: 2, name: 'test3', image: image },
              { id: 2, name: 'test4', image: image },
            ]"
            :attributes="['name']"
          >
            <template #left-side="{ item }">
              <img :src="item.image" />
            </template>
            <template #right-side="{ item }">
              <div>
                <Button
                  size="tiny"
                  icon="edit"
                  @click="alert('should edit item ' + item.name)"
                />
                <Button
                  size="tiny"
                  icon="trash"
                  @click="alert('should delete item ' + item.name)"
                />
              </div>
            </template>
          </List>
        </div>

        <div class="margin-bottom-3">
          <h2>Avatars</h2>
          <div style="display: flex; gap: 10px; padding: 0.5em">
            <Avatar size="tiny" icon="trash" />
            <Avatar size="tiny" icon="trash" color="warning" />
            <Avatar size="tiny" icon="trash" color="error" />
            <Avatar size="tiny" icon="trash" color="ghost" />
            <Avatar size="tiny" :image="image" color="ghost" />
            <Avatar size="tiny" initials="BW" color="ghost" />
            <Avatar size="tiny" icon="trash" :rounded="false" />
            <Avatar size="tiny" :image="image" color="ghost" :rounded="false" />
            <Avatar size="tiny" initials="BW" color="error" :rounded="false" />
          </div>
          <div style="display: flex; gap: 10px; padding: 0.5em">
            <Avatar icon="trash" />
            <Avatar :image="image" />
            <Avatar initials="BW" />
            <Avatar icon="trash" color="warning" />
            <Avatar :image="image" color="warning" />
            <Avatar initials="BW" color="warning" />
            <Avatar icon="trash" color="error" />
            <Avatar :image="image" color="error" />
            <Avatar initials="BW" color="error" />
          </div>
          <div style="display: flex; gap: 10px; padding: 0.5em">
            <Avatar icon="trash" color="ghost" />
            <Avatar :image="image" color="ghost" />
            <Avatar initials="BW" color="ghost" />
            <Avatar icon="trash" :rounded="false" />
            <Avatar :image="image" color="ghost" :rounded="false" />
            <Avatar initials="BW" color="error" :rounded="false" />
          </div>
          <div style="display: flex; gap: 10px; padding: 0.5em">
            <Avatar size="large" icon="trash" />
            <Avatar size="large" icon="trash" color="warning" />
            <Avatar size="large" icon="trash" color="error" />
            <Avatar size="large" icon="trash" color="ghost" />
            <Avatar size="large" :image="image" color="ghost" />
            <Avatar size="large" initials="BW" color="ghost" />
            <Avatar size="large" icon="trash" :rounded="false" />
            <Avatar
              size="large"
              :image="image"
              color="ghost"
              :rounded="false"
            />
            <Avatar size="large" initials="BW" color="error" :rounded="false" />
          </div>
        </div>
        <div class="margin-bottom-3">
          <h2>Presentations</h2>
          <Presentation
            title="My baserow integration"
            subtitle="Local baserow integration"
          />
          <Presentation
            title="My baserow integration"
            subtitle="Local baserow integration"
            initials="LB"
          />
          <Presentation
            title="My baserow integration"
            subtitle="Local baserow integration"
            icon="table"
          />
          <Presentation
            :image="image"
            title="My baserow integration"
            subtitle="Local baserow integration"
            avatar-color="ghost"
          />
          <Presentation
            :image="image"
            title="My baserow integration"
            subtitle="Local baserow integration with a very long description"
            avatar-color="ghost"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Toasts from '@baserow/modules/core/components/toasts/Toasts'
import AutoExpandableTextarea from '@baserow/modules/core/components/helpers/AutoExpandableTextarea'
import BaserowIcon from '@baserow/modules/core/static/img/logoOnly.svg'

export default {
  components: {
    Toasts,
    AutoExpandableTextarea,
  },
  data() {
    return {
      checkbox: false,
      radio: 'a',
      radioButton: 'a',
      switchValue: false,
      switchUnknown: 2,
      dropdown: '',
      longDropdown: '0',
      date: '',
      formula: 'concat(field("Text"), field("Text"))',
      image: BaserowIcon,
      input: '',
    }
  },
  head() {
    return {
      title: 'Style guide',
    }
  },
  methods: {
    alert(message) {
      alert(message)
    },
  },
}
</script>
