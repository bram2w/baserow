# Table of contents

Baserow is an open source online database tool. Users can use this no-code platform to
create a database without any technical experience. It lowers the threshold to a level
where everyone who can work with a spreadsheet can also create a database. The 
interface looks a lot like a spreadsheet. Our goal is to provide a perfect and fast 
user experience while keeping it easy for developers to write plugins and maintain the 
codebase. The developer documentation contains several topics you might need as a 
developer.

## Getting started

New to Baserow? This is the place to start.

* [Introduction](./getting-started/introduction.md): An introduction to some important
  concepts before using Baserow.
* [API](./getting-started/api.md): An introduction to the REST API and information 
  about API resources.
* [Database plugin](./getting-started/database-plugin.md) An introduction to the by 
  default installed database plugin.

## Guides

Need some help with setting things up?

* [Local demo](./guides/demo-environment.md): Run a local demo on your computer using 
  `docker-compose`.

## Development

Everything related to contributing and developing for Baserow.

* [Development environment](./development/development-environment.md): Setting up your
  local development environment using `docker-compose`.
* [Directory structure](./development/directory-structure.md): The structure of all the
  directories in the Baserow repository explained.
* [Tools](./development/tools.md): The tools (flake8, pytest, eslint, etc) and how to 
  use them. 
* [Code quality](./development/code-quality.md): More information about the the code 
  style, quality, choices and how we enforce them.

## Plugins

Everything related to custom plugin development.

* [Plugin basics](./plugins/introduction.md): An introduction into Baserow plugins.
* [Plugin boilerplate](./plugins/boilerplate.md): Don't reinvent the wheel, use
  the boilerplate for quick plugin development.
* [Create application](./plugins/application-type.md): Want to create an application 
  type? Here you find how to do that.
* [Create database table view](./plugins/view-type.md): Display table data like a 
  calendar, Kanban board or however you like by creating a view type.
* [Create database table field](./plugins/field-type.md): You can store data in a 
  custom format by creating a field type.
