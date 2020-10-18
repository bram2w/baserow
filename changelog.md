# Changelog

## Unreleased

* Fixed error when there is no view.
* Added Ubuntu installation guide documentation.
* Added Email field.

## Released (2020-10-06)

* Prevent adding a new line to the long text field in the grid view when selecting the
  cell by pressing the enter key.
* Fixed The table X is not found in the store error.
* Fixed bug where the selected name of the dropdown was not updated when that name was
  changed.
* Fixed bug where the link row field is not removed from the store when the related
  table is deleted.
* Added filtering of rows per view.
* Fixed bug where the error message of the 'Select a table to link to' was not always
  displayed.
* Added URL field.
* Added sorting of rows per view.

## Released (2020-09-02)

* Added contribution guidelines.
* Fixed bug where it was not possible to change the table name when it contained a link
  row field.

## Released (2020-08-31)

* Added field that can link to the row of another table.
* Fixed bug where the text_default value changed to None if not provided in a patch
  request.
* Block non web frontend domains in the base url when requesting a password reset
  email.
* Increased the amount of password characters to 256 when signing up.
* Show machine readable error message when the signature has expired.

## Released (2020-07-20)

* Added raises attribute to the docstrings.
* Added OpenAPI docs.
* Refactored all SCSS classes to BEM naming.
* Use the new long text field, date field and view's field options for the example 
  tables when creating a new account. Also use the long text field when creating a new 
  table.
* Removed not needed api v0 namespace in url and python module.
* Fixed keeping the datepicker visible in the grid view when selecting a date for the 
  first time.
* Improved API 404 errors by providing a machine readable error.
* Added documentation markdown files.
* Added cookiecutter plugin boilerplate.

## Released (2020-06-08)

* Fixed not handling 500 errors.
* Prevent row context menu when right clicking on a field that's being edited.
* Added row modal editing feature to the grid view.
* Made it possible to resize the field width per view.
* Added validation and formatting for the number field.
* Cancel the editing state of a fields when the escape key is pressed.
* The next field is now selected when the tab character is pressed when a field is
  selected.
* Changed the styling of the notification alerts.
* Fixed error when changing field type and the data value wasn't in the correct
  format.
* Update the field's data values when the type changes.
* Implemented reset forgotten password functionality.
* Fill a newly created table with some initial data.
* Enabled the arrow keys to navigate through the fields in the grid view.
* Fixed memory leak bug.
* Use environment variables for all settings.
* Normalize the users email address when signing up and signing in.
* Use Django REST framework status code constants instead of integers.
* Added long text field.
* Fixed not refreshing token bug and improved authentication a little bit.
* Introduced copy, paste and delete functionality of selected fields.
* Added date/datetime field.
* Improved grid view scrolling for touch devices.
* Implemented password change function and settings popup.
