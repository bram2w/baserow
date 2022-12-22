# Changelog

<!--
Ensure you add link to the gitlab issue if it exists at the end of your changelog line.
For example:

* My changelog line [(#123)](https://gitlab.com/bramw/baserow/-/issues/123)
-->

## Unreleased

### New Features

### Bug Fixes

### Refactors

## Released (2022-12-21 1.13.3)

## Deploy steps
* (Optional) - Regenerate the `card_cover` thumbnails to have better quality images in gallery views with: `./baserow regenerate_user_file_thumbnails card_cover`

### New Features

* (Enterprise Preview Feature) Database and Table level RBAC with Teams are now available as a preview feature for enterprise users, Add 'RBAC' to the FEATURE_FLAG env and restart var to enable.
* Possibility to disable password authentication if another authentication provider is enabled. [#1317](https://gitlab.com/bramw/baserow/-/issues/1317)
* Users with roles higher than viewer on tables and databases now counted as paid users
  on the enterprise plan including users who get those roles from a team.
  [#1322](https://gitlab.com/bramw/baserow/-/issues/1322)
* Add support for "Empty" and "Not Empty" filters for Collaborator field. [#1205](https://gitlab.com/bramw/baserow/-/issues/1205)
* The ordering APIs can now accept a partial list of ids to order only these ids.
* Add support for wildcard '*' in the FEATURE_FLAG env variable which enables all features.
* Added more Maths formula functions. [#1183](https://gitlab.com/bramw/baserow/-/issues/1183)

### Bug Fixes
* Fixed an issue where you would get an error if you accepted a group invitation with `NO_ACCESS` as you role [#1394](https://gitlab.com/bramw/baserow/-/issues/1394)
* Use the correct `OperationType` to restore rows [#1389](https://gitlab.com/bramw/baserow/-/issues/1389)
* Prevent zooming in when clicking on an input on mobile. [#722](https://gitlab.com/bramw/baserow/-/issues/722)
* Link/Lookup/Formula fields work again when restricting a users access to the related table [#1439](https://gitlab.com/bramw/baserow/-/issues/1439)

### Refactors
* Set a fixed width for `card_cover` thumbnails to have better-quality images. [#1278](https://gitlab.com/bramw/baserow/-/issues/#1278)

## Released (2022-12-8 1.13.2)

### New Features

* Add drag and drop zone for files to the row edit modal [#1161](https://gitlab.com/bramw/baserow/-/issues/1161)

* Automatically enable/disable enterprise features upon activation/deactivation without needing a page refresh first. [#1306](https://gitlab.com/bramw/baserow/-/issues/1306)
* Allow creating a new option by pressing enter in the dropdown [#1169](https://gitlab.com/bramw/baserow/-/issues/1169)
* Added the teams functionality as an enterprise feature. [#1226](https://gitlab.com/bramw/baserow/-/issues/1226)
* Improved grid view on smaller screens by not making the primary field sticky. [#690](https://gitlab.com/bramw/baserow/-/issues/690)
* New items automatically get a new name in the modal. [1166](https://gitlab.com/bramw/baserow/-/issues/1166)
* Don't require password verification when deleting user account. [#1401](https://gitlab.com/bramw/baserow/-/issues/1401)

### Bug Fixes
* Fixed the Heroku deployment template. [#1420](https://gitlab.com/bramw/baserow/-/issues/1420)
* Fixed bug where only one condition per field was working in form's views. [#1400](https://gitlab.com/bramw/baserow/-/issues/1400)
* Fix "ERR_REDIRECT" for authenticated users redirected to the dashboard from the signup page. [1125](https://gitlab.com/bramw/baserow/-/issues/1125)
* Fixed a problem of some specific error messages not being recognized by the web front-end.

* Fixed failing webhook call log creation when a table has more than one webhooks. [#1100](https://gitlab.com/bramw/baserow/-/merge_requests/1100)

### Refactors
* Refresh the JWT token when needed instead of periodically. [#1294](https://gitlab.com/bramw/baserow/-/issues/1294)
* Remove "// Baserow" from title on a publicly shared view if `show_logo` is set to false. [#1378](https://gitlab.com/bramw/baserow/-/issues/1378)

## Released (2022-11-22 1.13.1)

### New Features

* OAuth 2 flows now support redirects to specific pages. [#1288](https://gitlab.com/bramw/baserow/-/issues/1288)
* Add support for language selection and group invitation tokens for OAuth 2 and SAML. [#1293](https://gitlab.com/bramw/baserow/-/issues/1293)
* Implemented the option to start direct support if the instance is on the enterprise plan.
* Calendar / date field picker: Highlight the current date and weekend [#1128](https://gitlab.com/bramw/baserow/-/issues/1128)
* Made it possible to optionally hide fields in a publicly shared form by providing the `hide_FIELD` query parameter. [#1096](https://gitlab.com/bramw/baserow/-/issues/1096)

### Bug Fixes

* Standardize the API documentation "token" references.
* Raise an exception when a user doesn't have a required feature on an endpoint
* Fixed authenticated state changing before redirected to the login page when logging off. [#1328](https://gitlab.com/bramw/baserow/-/issues/1328)
* `permanently_delete_marked_trash` task no longer fails on permanently deleting a table before an associated rows batch.  [#1266](https://gitlab.com/bramw/baserow/-/issues/1266)
* Fixed bug where "add filter" link was not clickable if the primary field has no compatible filter types. [#1302](https://gitlab.com/bramw/baserow/-/issues/1302)
* Fixed OAuth 2 flows for providers that don't provide user's name. Email will be used as a temporary placeholder so that an account can be created.  [#1371](https://gitlab.com/bramw/baserow/-/issues/1371)

### Refactors

* Changed `TableGroupStorageUsageItemType.calculate_storage_usage` to use a PL/pgSQL function to speedup the storage usage calculation.
* Replace the CSS classes for SSO settings forms. [#1336](https://gitlab.com/bramw/baserow/-/issues/1336)
* Moved the Open Sans font to the static directory instead of a Google fonts dependency. [#1246](https://gitlab.com/bramw/baserow/-/issues/1246)

### Breaking Changes

## Released (2022-11-02 1.13.0)

### New Features

* Background pending tasks like duplication and template_install are restored in a new frontend session if unfinished. [#885](https://gitlab.com/bramw/baserow/-/issues/885)
* Added Zapier integration code. [#816](https://gitlab.com/bramw/baserow/-/issues/816)
* Made it possible to filter on the `created_on` and `updated_on` columns, even though
  they're not exposed via fields.
* Expose `read_only` in the list fields endpoint.
* Made it possible to add additional signup step via plugins.
* Add an option to remove the Baserow logo from your public view. [#1203](https://gitlab.com/bramw/baserow/-/issues/1203)
* Always allow the cover image of a gallery view to be accessible by a public view [#1113](https://gitlab.com/bramw/baserow/-/issues/1113).
* Added the ability to double click a grid field name so that quick edits can be made. [#1147](https://gitlab.com/bramw/baserow/-/issues/1147).
* Upgraded docker containers base images from `debian:buster-slim` to the latest stable `debian:bullseye-slim`.
* Upgraded python version from `python-3.7.16` to `python-3.9.2`.
* Added SAML protocol implementation for Single Sign On as an enterprise feature. [#1227](https://gitlab.com/bramw/baserow/-/issues/1227)
* Added OAuth2 support for Single Sign On with Google, Facebook, GitHub, and GitLab as preconfigured providers. Added general support for OpenID Connect. [#1254](https://gitlab.com/bramw/baserow/-/issues/1254)

### Bug Fixes

* Fixed bug where it was not possible to select text in a selected and editing cell in Chrome. [#1234](https://gitlab.com/bramw/baserow/-/issues/1234)
* Fixed bug where the row metadata was not updated when receiving a realtime event.
* Duplicating a table with a removed single select option value no longer results in an error. [#1263](https://gitlab.com/bramw/baserow/-/issues/1263)
* Selecting text in models, contexts, form fields and grid view cells no longer unselects when releasing the mouse outside. [#1243](https://gitlab.com/bramw/baserow/-/issues/1243)
* Fixed slug rotation for GalleryView. [#1232](https://gitlab.com/bramw/baserow/-/issues/1232)

### Refactors

* Replace members modal with a new settings page. [#1229](https://gitlab.com/bramw/baserow/-/issues/1229)
* Frontend now install templates as an async job in background instead of using a blocking call. [#885](https://gitlab.com/bramw/baserow/-/issues/885)
* Changed the add label of several buttons.

### Breaking Changes

* Changed error codes returned by the premium license API endpoints to replacing `PREMIUM_LICENSE` with `LICENSE`. [#1230](https://gitlab.com/bramw/baserow/-/issues/1230)
* List jobs endpoint "list_job" returns now an object with jobs instead of a list of jobs. [#885](https://gitlab.com/bramw/baserow/-/issues/885)
* The "token_auth" endpoint response and "user_data_updated" messages now have an "active_licenses" key instead of "premium" indicating what licenses the user has active. [#1230](https://gitlab.com/bramw/baserow/-/issues/1230)
* Changed the JWT library to fix a problem causing the refresh-tokens not working properly. [#787]https://gitlab.com/bramw/baserow/-/issues/787)

## Released (2022-09-20 1.12.1)

### New Features

* Made it possible to share the Kanban view publicly. [#1146](https://gitlab.com/bramw/baserow/-/issues/1146)
* New templates:
    * Copy Management
    * Hiking Guide
    * New Hire Onboarding
    * Property Showings
    * QA Test Scripts
    * Risk Assessment and Management
    * Web App UAT
* Updated templates:
    * Benefit Show Manager
    * Car Hunt
    * Wedding Client Planner
* Added link, button, get_link_label and get_link_url formula functions. [#818](https://gitlab.com/bramw/baserow/-/issues/818)
* Show database and table duplication progress in the left sidebar. [#1059](https://gitlab.com/bramw/baserow/-/issues/1059)
* Add env vars for controlling which URLs and IPs webhooks are allowed to use. [#931](https://gitlab.com/bramw/baserow/-/issues/931)
* Add a rich preview while importing data to an existing table. [#1120](https://gitlab.com/bramw/baserow/-/issues/1120)
* Always allow the cover image of a gallery view to be accessible by a public view [#1113](https://gitlab.com/bramw/baserow/-/issues/1113).
* Added support for placeholders in form headings and fields. [#1168](https://gitlab.com/bramw/baserow/-/issues/1168)

### Bug Fixes
* Always allow the cover image of a gallery view to be accessible by a public view [#1113](https://gitlab.com/bramw/baserow/-/issues/1113).
* Fixed Multiple Collaborators field renames. Now renaming the field won't recreate the field so that data is preserved.
* Fixed a bug that breaks the link row modal when a formula is referencing a single select field. [#1111](https://gitlab.com/bramw/baserow/-/issues/1111)
* Fixed an issue where customers with malformed file extensions were unable to snapshot or duplicate properly [#1194](https://gitlab.com/bramw/baserow/-/issues/1194).
* Plugins can now change any and all Django settings instead of just the ones set previously by Baserow.
* Static files collected from plugins will now be correctly served. 
* The /admin url postfix will now be passed through to the backend API for plugins to use.

### Refactors

* Formulas which referenced other aggregate formulas now will work correctly. [#1081](https://gitlab.com/bramw/baserow/-/issues/1081)
* Improved file import UX for existing table. [#1120](https://gitlab.com/bramw/baserow/-/issues/1120)

### Refactors

* Used SimpleGrid component for SelectRowModal. [#1120](https://gitlab.com/bramw/baserow/-/issues/1120)

## Released (2022-09-07 1.12.0)

### New Features

* Added Multiple Collaborators field type. [#1119](https://gitlab.com/bramw/baserow/-/issues/1119)
* Added missing success printouts to `count_rows` and `calculate_storage_usage` commands.
* Add `isort` settings to sort python imports.
* Add row url parameter to `gallery` and `kanban` view.
* Add navigation buttons to the `RowEditModal`.
* Introduced a premium form survey style theme. [#524](https://gitlab.com/bramw/baserow/-/issues/524).
* Allow creating new rows when selecting a related row [#1064](https://gitlab.com/bramw/baserow/-/issues/1064).
* Add row url parameter to `gallery` and `kanban` view.
* Enable `file field` in `form` views. [#525](https://gitlab.com/bramw/baserow/-/issues/525)
* Only allow relative urls in the in the original query parameter.
* Force browser language when viewing a public view. [#834](https://gitlab.com/bramw/baserow/-/issues/834)
* Search automatically after 400ms when chosing a related field via the modal. [#1091](https://gitlab.com/bramw/baserow/-/issues/1091)
* Add cancel button to field update context [#1020](https://gitlab.com/bramw/baserow/-/issues/1020)
* Sort fields on row select modal by the order of the first view in the related table. [#1062](https://gitlab.com/bramw/baserow/-/issues/1062)
* New signals `user_updated`, `user_deleted`, `user_restored`, `user_permanently_deleted` were added to track user changes.
* `list_groups` endpoint now also returns the list of all group users for each group.
* Fields can now be duplicated with their cell values also. [#964](https://gitlab.com/bramw/baserow/-/issues/964)
* Add a tooltip to applications and tables in the left sidebar to show the full name. [#986](https://gitlab.com/bramw/baserow/-/issues/986)
* Allow not creating a reversed relationship with the link row field. [#1063](https://gitlab.com/bramw/baserow/-/issues/1063)
* Add API token authentication support to multipart and via-URL file uploads. [#255](https://gitlab.com/bramw/baserow/-/issues/255)

### Bug Fixes
* Resolve circular dependency in `FieldWithFiltersAndSortsSerializer` [#1113](https://gitlab.com/bramw/baserow/-/issues/1113)
* Fix various misspellings. Contributed by [@Josh Soref](https://github.com/jsoref/) using [check-spelling.dev](https://check-spelling.dev/)
* Fixed a bug when importing Airtable base with a date field less than 1000. [#1046](https://gitlab.com/bramw/baserow/-/issues/1046)
* Prefetch field options on views that are iterated over on field update realtime events [#1113](https://gitlab.com/bramw/baserow/-/issues/1113)
* Clearing cell values multi-selected from right to left with backspace shifts selection to the right and results in wrong deletion. [#1134](https://gitlab.com/bramw/baserow/-/issues/1134)
* Fixed a bug that prevent to use arrows keys in the grid view when a formula field is selected. [#1136](https://gitlab.com/bramw/baserow/-/issues/1136)
* Fixed a bug that make the grid view crash when searching text and a formula field is referencing a singe-select field. [#1110](https://gitlab.com/bramw/baserow/-/issues/1110)
* Fixed horizontal scroll on Mac OSX.
* Fixed bug where the row coloring didn't work in combination with group level premium.
* Fixed bug where the link row field lookup didn't work in combination with password 
  protected views.
* "Link to table" field does not allow submitting empty values. [#1159](https://gitlab.com/bramw/baserow/-/issues/1159)
* Fixed bug where the "Create option" button was not visible for the single and multiple
  select fields in the row edit modal.
* Resolve an issue with uploading a file via a URL when it contains a querystring. [#1034](https://gitlab.com/bramw/baserow/-/issues/1034)
* Resolve an invalid URL in the "Backend URL mis-configuration detected" error message. [#967](https://gitlab.com/bramw/baserow/-/merge_requests/967)
* Fixed broken call grouping when getting linked row names from server.
* Add new filter types 'is after today' and 'is before today'. [#1093](https://gitlab.com/bramw/baserow/-/issues/1093)

### Refactors
* Fix view and fields getting out of date on realtime updates. [#1112](https://gitlab.com/bramw/baserow/-/issues/1112)
* Make it possible to copy/paste/import from/to text values for multi-select and file fields. [#913](https://gitlab.com/bramw/baserow/-/issues/913)
* Users can copy/paste images into a file field. [#367](https://gitlab.com/bramw/baserow/-/issues/367)
* Fixed error when sharing a view publicly with sorts more than one multi-select field. [#1082](https://gitlab.com/bramw/baserow/-/issues/1082)
* Fixed crash in gallery view with searching. [#1130](https://gitlab.com/bramw/baserow/-/issues/1130)

### Breaking Changes

* The export format of file fields has changed for CSV files. The new format is `fileName1.ext (file1url),fileName2.ext (file2url), ...`.
* The date parsing takes the date format into account when parsing unless the format respect the ISO-8601 format. This will change the value for ambiguous dates like `02/03/2020`.

## Released (2022-07-27 1.11.0)

### New Features

* Add configs and docs for VSCode setup. [#854](https://gitlab.com/bramw/baserow/-/issues/854)
* Added `in this week` filter [#569](https://gitlab.com/bramw/baserow/-/issues/954).
* Allow users to use row id in the form redirect URL. [#871](https://gitlab.com/bramw/baserow/-/merge_requests/871)
* Added a new "is months ago filter". [#1018](https://gitlab.com/bramw/baserow/-/issues/1018)
* Added a new "is years ago filter". [#1019](https://gitlab.com/bramw/baserow/-/issues/1019)
* Conditionally show form fields.
* Show badge when the user has account level premium.
* Added a new `ClientUndoRedoActionGroupId` request header to bundle multiple actions in a single API call. [#951](https://gitlab.com/bramw/baserow/-/issues/951)
* Applications can now be duplicated. [#960](https://gitlab.com/bramw/baserow/-/issues/960)
* Added option to use view's filters and sorting when listing rows. [#190](https://gitlab.com/bramw/baserow/-/issues/190)
* Added public gallery view [#1057](https://gitlab.com/bramw/baserow/-/issues/1057)
* Fixed bug with 404 middleware returning different 404 error messages based on the endpoint.
* Made it possible to import data into an existing table. [#342](https://gitlab.com/bramw/baserow/-/issues/342)
* New templates:
    * Benefit Show Manager
    * Business Expenses
    * Emergency Triage Log
    * Employee Directory
    * Growth Experiments
    * Moving Company Manager
    * Online Freelancer Management
    * Personal Finance Manager
    * User Feedback
    * Workshops and Trainings
* Updated templates:
    * Company Blog Management
    * Student Planner
    * Applicant Tracker
    * Book Catalog
    * Bucket List
    * Car Maintenance Log
    * Company Asset Tracker
    * Email Marketing Campaigns
    * Holiday Shopping
    * Recipe Book
    * Wedding Planning
* Tables can now be duplicated. [#961](https://gitlab.com/bramw/baserow/-/issues/961)
* Introduced environment variable to disable Google docs file preview. [#1074](https://gitlab.com/bramw/baserow/-/issues/1074)
* Made it possible to select the entire row via the row context menu. [#1061](https://gitlab.com/bramw/baserow/-/issues/1061)
* Show modal when the users clicks on a deactivated premium features. [#1066](https://gitlab.com/bramw/baserow/-/issues/1066)
* Replaced all custom alert code with `Alert` component [#1016](https://gitlab.com/bramw/baserow/-/issues/1016)
* Add ability to create and restore snapshots. [#141](https://gitlab.com/bramw/baserow/-/issues/141)
* When viewing an expanded row switch to a unique URL which links to that row. [#938](https://gitlab.com/bramw/baserow/-/issues/938)

### Bug Fixes

* Disable table import field type guessing and instead always import as text fields. [#1050](https://gitlab.com/bramw/baserow/-/issues/1050)
* Upgrade the images provided in our example docker-compose files to be the latest and most secure. [#1056](https://gitlab.com/bramw/baserow/-/issues/1056)
* Fix the perm delete trash cleanup job failing for self linking tables. [#1075](https://gitlab.com/bramw/baserow/-/issues/1075)
* Add better error handling to row count job. [#1051](https://gitlab.com/bramw/baserow/-/issues/1051)
* Fixed changing field type to unsupported form view bug. [#1078](https://gitlab.com/bramw/baserow/-/issues/1078)
* Ensure the latest error is always shown when clicking the formula refresh options link. [#1092](https://gitlab.com/bramw/baserow/-/issues/1092)
* Fixed duplicating view with that depends on select options mapping. [#1104](https://gitlab.com/bramw/baserow/-/issues/1104)
* Don't allow invalid aggregate formulas from being created causing errors when inserting rows. [#1089](https://gitlab.com/bramw/baserow/-/issues/1089)
* Fix backspace and delete keys breaking after selecting a formula text cell. [#1085](https://gitlab.com/bramw/baserow/-/issues/1085)
* Fixed problem when new webhooks would be sent twice with both old and new payload.
* Fixed problem causing kanban view duplication to fail silently. [#1109](https://gitlab.com/bramw/baserow/-/issues/1109)
* Display round and trunc functions in the formula edit modal, rename int to trunc and make these functions handle weird inputs better. [#1095](https://gitlab.com/bramw/baserow/-/issues/1095)
* Fix some rare errors when combining the if and divide formula functions. [#1086](https://gitlab.com/bramw/baserow/-/issues/1086)

### Breaking Changes

* API endpoints `undo` and `redo` now returns a list of actions undone/redone instead of a single action.
* Removed `primary` from all `components`and `stores` where it isn't absolutely required. [#1057](https://gitlab.com/bramw/baserow/-/issues/1057)
* Concurrent field updates will now respond with a 409 instead of blocking until the previous update finished, set the env var BASEROW_WAIT_INSTEAD_OF_409_CONFLICT_ERROR to revert to the old behaviour. [#1097](https://gitlab.com/bramw/baserow/-/issues/1097)

* **breaking change** Webhooks `row.created`, `row.updated` and `row.deleted` are
  replaced with `rows.created`, `rows.updated` and `rows.deleted`, containing multiple
  changed rows at once. Already created webhooks will still be called, but the received
  body will contain only the first changed row instead of all rows. It is highly
  recommended to convert all webhooks to the new types.
* Fix not being able to paste multiple cells when a formula field of array or single select type was in an error state. [#1084](https://gitlab.com/bramw/baserow/-/issues/1084)
* API endpoint `/database/views/grid/${viewSlug}/public/info/` has been replaced by `/database/views/${viewSlug}/public/info/` [#1057](https://gitlab.com/bramw/baserow/-/issues/1057)
  recommended converting all webhooks to the new types.


## Released (2022-07-05 1.10.2)

### New Features

* Added prefill query parameters for forms. [#852](https://gitlab.com/bramw/baserow/-/issues/852)
* Added Link Row contains filter. [874](https://gitlab.com/bramw/baserow/-/issues/874)
* Made the styling of the dashboard cleaner and more efficient.
  [#1023](https://gitlab.com/bramw/baserow/-/issues/1023)
* Added possibility to delete own user account [#880](https://gitlab.com/bramw/baserow/-/issues/880)
* Added new `group_user_added` signal that is called when an user accept an invitation to join a group.
* Added new `before_group_deleted` signal that is called just before a group would end up in the trash.
* Added multi-cell clearing via backspace key (delete on Mac).
* Added API exception registry that allows plugins to provide custom exception mappings for the REST API.
* Added formula round and int functions. [#891](https://gitlab.com/bramw/baserow/-/issues/891)
* Views can be duplicated. [#962](https://gitlab.com/bramw/baserow/-/issues/962)
* Link to table field can now link rows in the same table. [#798](https://gitlab.com/bramw/baserow/-/issues/798)
* Made it clearer that you're navigating to baserow.io when clicking the "Get a license"
  button.
* Redirect to signup instead of the login page if there are no admin users. [#1035](https://gitlab.com/bramw/baserow/-/issues/1035)
* `./dev.sh all_in_one_dev` now starts a hot reloading dev mode using the all-in-one image.
* Add startup check ensuring BASEROW_PUBLIC_URL and related variables are correct. [#1041](https://gitlab.com/bramw/baserow/-/issues/1041)
* Made it possible to extend the register page.
* Made it possible to extend the app layout.
* Allow to import more than 15Mb. [949](ttps://gitlab.com/bramw/baserow/-/issues/949)
* Add the ability to disable the model cache with the new BASEROW_DISABLE_MODEL_CACHE env variable.
* Add support for horizontal scrolling in grid views pressing Shift + mouse-wheel. [#867](https://gitlab.com/bramw/baserow/-/issues/867)
* Add basic field duplication. [#964](https://gitlab.com/bramw/baserow/-/issues/964)

### Bug Fixes

* Upload modal no longer closes when removing a file. [#569](https://gitlab.com/bramw/baserow/-/issues/569)
* API returns a nicer error if URL trailing slash is missing. [798](https://gitlab.com/bramw/baserow/-/issues/798)
* Fix dependant fields not being updated if the other side of a link row field changed. [918](https://gitlab.com/bramw/baserow/-/issues/918)
* Fix nested aggregate formulas not calculating results or causing errors. [683](https://gitlab.com/bramw/baserow/-/issues/683)
* Fix regex_replace formula function allowing invalid types as params. [#1024](https://gitlab.com/bramw/baserow/-/issues/1024)
* Fix newly imported templates missing field dependencies for some link row fields. [#1025](https://gitlab.com/bramw/baserow/-/issues/1025)
* Fix converting a link row not updating dependants on the reverse side. [#1026](https://gitlab.com/bramw/baserow/-/issues/1026)
* Fix formula bugs caused by unsupported generation of BC dates. [#952](https://gitlab.com/bramw/baserow/-/issues/952)
* Fix formula bug caused when looking up date intervals. [#924](https://gitlab.com/bramw/baserow/-/issues/924)
* Treat null values as zeros for numeric formulas. [#886](https://gitlab.com/bramw/baserow/-/issues/886)
* Add debugging commands/options for inspecting tables and updating formulas.
* Fix rare formula bug with multiple different formulas and view filters in one table. [#801](https://gitlab.com/bramw/baserow/-/issues/801)
* Added FormulaField to the options for the primary field. [#859](https://gitlab.com/bramw/baserow/-/issues/859)
* Fix errors when using row_id formula function with left/right functions.
* Fixed URL fields not being available in lookup fields. [#984](https://gitlab.com/bramw/baserow/-/issues/984)
* Fix lookup field conversions deleting all of its old field dependencies. [#1036](https://gitlab.com/bramw/baserow/-/issues/1036)
* Fix views becoming inaccessible due to race condition when invalidating model cache. [#1040](https://gitlab.com/bramw/baserow/-/issues/1040)
* Fix refresh formula options button always being shown initially. [#1037](https://gitlab.com/bramw/baserow/-/issues/1037)
* Fix get_human_readable_value crashing for some formula types. [#1042](https://gitlab.com/bramw/baserow/-/issues/1042)
* Fix import form that gets stuck in a spinning state when it hits an error.

### Breaking Changes

## Released (2022-06-09 1.10.1)

* Plugins can now include their own menu or other template in the main menu sidebar.
* Added the ability to use commas as separators in number fields
* Shift+Enter on grid view exit from editing mode for long text field
* Shift+Enter on grid view go to field below
* Make fields sortable in row create/edit modal.
* Added row coloring for Kanban and Gallery views
* Duplicate row.
* Added multi-row delete.
* Added a dropdown to the grid view that allows you to
  select the type of row identifier displayed next to a row (`Count`or `Row Identifier`).
* Added an admin setting to disable the ability to reset a users password.
* Fix formula bug caused when arguments of `when_empty` have different types.
* Formulas of type text now use textarea to show the cell value.
* Fix a bug in public grid views that prevented expanding long-text cells.
* Deprecate the SYNC_TEMPLATES_ON_STARTUP environment variable and no longer call the
  sync_templates command on startup in the docker images.
* Added BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION environment variable and now
  do the sync_templates task in the background after migration to massively speedup 
  first time Baserow startup speed.
* Fix deadlocks and performance problems caused by un-needed accidental row locks.
* Fixed CSV import adding an extra row with field names if the no headers option is selected.
* Fixed bad request displayed with webhook endpoints that redirects
* **breaking change** The API endpoint `/api/templates/install/<group_id>/<template_id>/`
  is now a POST request instead of GET.

## Released (2022-10-05 1.10.0)
* Prevent the Airtable import from failing hard when an invalid date is provided.
* Increased the max decimal places of a number field to 10.
* Fix formula autocomplete for fields with multiple quotes
* Fix slowdown in large Baserow instances as the generated model cache got large.
* The standalone `baserow/backend` image when used to run a celery service now defaults
  to running celery with the same number of processes as the number of available cores.
* When the BASEROW_AMOUNT_OF_WORKERS env variable is set to blank, the amount of worker
  processes defaults to the number of available cores.
* Fixed bug preventing file uploads via an url for self-hosters 
* Added new environment variable BASEROW_FILE_UPLOAD_SIZE_LIMIT_MB
* Fix aggregation not updated on filter update
* Fixed plugin boilerplate guide.

## Released (2022-10-05 1.10.0)

* Added batch create/update/delete rows endpoints. These endpoints make it possible to
  modify multiple rows at once. Currently, row created, row updated, and row deleted 
  webhooks are not triggered when using these endpoints.
* Fixed translations in emails sent by Baserow.
* Fixed invalid `first_name` validation in the account form modal.
* Shared public forms now don't allow creating new options
  for single and multiple select fields.
* Fixed bug where the arrow keys of a selected cell didn't work when they were not
  rendered.
* Select new view immediately after creation.
* Added group context menu to sidebar.
* Fixed Airtable import bug where the import would fail if a row is empty.
* Fixed occasional UnpicklingError error when getting a value from the model cache. 
* Fixed a problem where a form view with link row fields sends duplicate lookup requests.
* Pin backend python dependencies using pip-tools.
* Fixed the reactivity of the row values of newly created fields in some cases.
* Made it possible to impersonate another user as premium admin.
* Added `is days ago` filter to date field.
* Fixed a bug that made it possible to delete created on/modified by fields on the web frontend.
* Allow the setting of max request page size via environment variable.
* Added select option suggestions when converting to a select field.
* Introduced read only lookup of foreign row by clicking on a link row relationship in 
  the grid view row modal.
* Boolean field converts the word `checked` to `True` value.
* Fixed a bug where the backend would fail hard updating token permissions for deleted tables.
* Fixed the unchecked percent aggregation calculation
* Raise Airtable import task error and fixed a couple of minor import bugs.
* Add loading bar when syncing templates to make it obvious Baserow is still loading.
* Fixed bug where old values are missing in the update trigger of the webhook.
* Scroll to the first error message if the form submission fail
* Improved backup_baserow splitting multiselect through tables in separate batches.
* Fixed a bug that truncated characters for email in the sidebar
* **breaking change** The API endpoint `/api/database/formula/<field_id>/type/` now requires
  `table_id` instead of `field_id`, and also `name` in the request body.
* Added support in dev.sh for KDE's Konsole terminal emulator.
* Fixed a bug that would sometimes cancel multi-cell selection.
* Upgraded node runtime to v16.14.0
* Cache aggregation values to improve performances
* Added new endpoint to get all configured aggregations for a grid view
* Fixed DONT_UPDATE_FORMULAS_AFTER_MIGRATION env var not working correctly.
* Stopped the generated model cache clear operation also deleting all other redis keys.
* Added Spanish and Italian languages.
* Added undo/redo.
* Fixed bug where the link row field `link_row_relation_id` could fail when two 
  simultaneous requests are made.
* Added password protection for publicly shared grids and forms.
* Added multi-cell pasting.
* Made views trashable.
* Fixed bug where a cell value was not reverted when the request to the backend fails.
* **Premium** Added row coloring.
* Fixed row coloring bug when the table doesn't have any single select field.
* Dropdown can now be focused with tab key
* Added 0.0.0.0 and 127.0.0.1 as ALLOWED_HOSTS for connecting to the Baserow backend
* Added a new BASEROW_EXTRA_ALLOWED_HOSTS optional comma separated environment variable
  for configuring ALLOWED_HOSTS.
* Fixed a bug for some number filters that causes all rows to be returned when text is entered.
* Fixed webhook test call failing when request body is empty.
* Fixed a bug where making a multiple cell selection starting from an 
  empty `link_row` or `formula` field was not possible in Firefox.
* New templates:
  * Brand Assets Manager
  * Business Conference
  * Car Hunt
  * Company Blog Management
  * Event Staffing
  * Hotel Bookings
  * Nonprofit Grant Tracker
  * Performance Reviews
  * Product Roadmap
  * Public Library Inventory
  * Remote Team Hub
  * Product Roadmap
  * Hotel Bookings
* Updated templates:
  * Book writing guide
  * Bucket List
  * Call Center Log
  * Company Asset Tracker
  * Email Marketing Campaigns
  * Home Inventory
  * House Search
  * Job Search
  * Nonprofit Organization Management
  * Personal Task Manager
  * Political Campaign Contributions
  * Project Tracker
  * Recipe Book
  * Restaurant Management
  * Single Trip Planner
  * Software Application Bug Tracker
  * Student Planner
  * Teacher Lesson Plans
  * Team Check-ins
  * University Admissions Management
  * Wedding Client Planner


## Released (2022-03-03 1.9.1)

* Fixed bug when importing a formula or lookup field with an incorrect empty value.
* New templates:
    * Non-profit Organization Management
    * Elementary School Management
    * Call Center Log
    * Individual Medical Record
    * Trip History
    * Favorite Food Places
    * Wedding Client Planner
* Updated templates:
    * Holiday Shopping
    * Company Asset Tracker
    * Personal Health Log
    * Recipe Book
    * Student Planner
    * Political Campaign Contributions
* Upgraded `drf-spectacular`. Flag-style query parameters like `count` will now be displayed
  as `boolean` instead of `any` in the OpenAPI documentation. However, the behavior of these 
  flags is still the same.
* Fixed API docs enum warnings. Removed `number_type` is no longer displayed in the API docs.
* Fix the Baserow Heroku install filling up the hobby postgres by disabling template 
  syncing by default.

## Released (2022-03-02 1.9)

* Added accept `image/*` attribute to the form cover and logo upload. 
* Added management to import a shared Airtable base.
* Added web-frontend interface to import a shared Airtable base.
* Fixed adding new fields in the edit row popup that require refresh in Kanban and Form views.
* Cache model fields when generating model.
* Fixed `'<' not supported between instances of 'NoneType' and 'int'` error. Blank 
  string for a decimal value is now converted to `None` when using the REST API.
* Moved the in component `<i18n>` translations to JSON files. 
* Fix restoring table linking to trashed tables creating invalid link field. 
* Fixed not being able to create or convert a single select field with edge case name.
* Add Kanban view filters.
* Fix missing translation when importing empty CSV
* Fixed OpenAPI spec. The specification is now valid and can be used for imports to other
  tools, e.g. to various REST clients.
* Added search to gallery views.
* Views supporting search are properly updated when a column with a matching default value is added.
* Allow for group registrations while public registration is closed
* Allow for signup via group invitation while public registration is closed.
* **breaking change** Number field has been changed and doesn't use `number_type` property 
  anymore. The property `number_decimal_places` can be now set to `0` to indicate integers
  instead.
* Fixed error when the select row modal is closed immediately after opening.
* Add footer aggregations to grid view
* Hide "Export view" button if there is no valid exporter available
* Fix Django's default index naming scheme causing index name collisions.
* Added multi-cell selection and copying.
* Add "insert left" and "insert right" field buttons to grid view head context buttons.
* Workaround bug in Django's schema editor sometimes causing incorrect transaction 
  rollbacks resulting in the connection to the database becoming unusable.
* Rework Baserow docker images so they can be built and tested by gitlab CI.
* Bumped some backend and web-frontend dependencies.
* Remove runtime mjml service and pre-render email templates at build time.
* Add the all-in-one Baserow docker image.
* Migrate the Baserow Cloudron and Heroku images to work from the all-in-one.
* **breaking change** docker-compose.yml now requires secrets to be setup by the user,
  listens by default on 0.0.0.0:80 with a Caddy reverse proxy, use BASEROW_PUBLIC_URL 
  and BASEROW_CADDY_ADDRESSES now to configure a domain with optional auto https.
* Add health checks for all services.
* Ensure error logging is enabled in the Backend even when DEBUG is off.
* Removed upload file size limit.

## Released (2022-01-13 1.8.2)

* Fix Table Export showing blank modal.
* Fix vuelidate issues when baserow/web-frontend used as dependency. 

## Released (2022-01-13 1.8.1)

* Fixed migration failing when upgrading a version of Baserow installed using Postgres 
  10 or lower.
* Fixed download/preview files from another origin

## Released (2022-01-13)

* Fixed frontend errors occurring sometimes when mass deleting and restoring sorted 
  fields
* Added French translation.
* Added Video, Audio, PDF and some Office file preview.
* Added rating field type.
* Fix deleted options that appear in the command line JSON file export.
* Fix subtracting date intervals from dates in formulas in some situations not working.
* Added day of month filter to date field.
* Added gallery view.
  * Added cover field to the gallery view.
* Added length is lower than filter.
* **dev.sh users** Fixed bug in dev.sh where UID/GID were not being set correctly, 
  please rebuild any dev images you are using.
* Replaced the table `order` index with an `order, id` index to improve performance.
* **breaking change** The API endpoint to rotate a form views slug has been moved to
  `/database/views/${viewId}/rotate-slug/`.
* Increased maximum length of application name to 160 characters.
* Fixed copying/pasting for date field.
* Added ability to share grid views publicly.
* Allow changing the text of the submit button in the form view.
* Fixed reordering of single select options when initially creating the field.
* Improved performance by not rendering cells that are out of the view port.
* Fix bug where field options in rare situations could have been duplicated.
* Focused the search field when opening the modal to link a table row.
* Fixed order of fields in form preview.
* Fix the ability to make filters and sorts on invalid formula and lookup fields.
* Fixed bug preventing trash cleanup job from running after a lookup field was converted
  to another field type.
* Added cover field to the Kanban view.
* Fixed bug where not all rows were displayed on large screens.
* New templates:
    * Car Maintenance Log
    * Teacher Lesson Plans
    * Business Conference Event
    * Restaurant Management
* Updated templates:
    * Healthcare Facility Management
    * Apartment Hunt
    * Recipe Book
    * Commercial Property Management

## Released (2021-11-25)

* Increase Webhook URL max length to 2000.
* Fix trashing tables and related link fields causing the field dependency graph to
  become invalid.
* Fixed not executing premium tests.

## Released (2021-11-24)

* Fixed a bug where the frontend would fail hard if a table with no views was accessed.
* Tables can now be opened in new browser tabs.
* **Breaking Change**: Baserow's `docker-compose.yml` now allows setting the MEDIA_URL
  env variable. If using MEDIA_PORT you now need to set MEDIA_URL also.
* **Breaking Change**: Baserow's `docker-compose.yml` container names have changed to
  no longer be hardcoded to prevent naming clashes.
* Added a licensing system for the premium version.
* Fixed bug where it was possible to create duplicate trash entries.
* Fixed propType validation error when converting from a date field to a boolean field.
* Deprecate internal formula field function field_by_id.
* Made it possible to change user information.
* Added table webhooks functionality.
* Added extra indexes for user tables increasing performance.
* Add lookup field type.
* Add aggregate formula functions and the lookup formula function.
* Fixed date_diff formula function.
* Fixed a bug where the frontend would fail hard when converting a multiple select field
  inside the row edit modal.
* Added the kanban view.
* New templates:
    * House Search
    * Personal Health Log
    * Job Search
    * Single Trip Planner
    * Software Application Bug Tracker
* Updated templates:
    * Commercial Property Management
    * Company Asset Tracker
    * Wedding Planner
    * Blog Post Management
    * Home Inventory
    * Book Writing Guide
    * Political Campaign Contributions
    * Applicant Tracker

## Released (2021-10-05)

* Introduced new endpoint to get and update user account information.
* Fixed bug where a user could not be edited in the admin interface without providing 
  a password.
* Fixed bug where sometimes fields would not be ordered correctly in view exports.
* Fixed bug where brand-new fields weren't included in view exports.
* Fixed error when pasting into a single select field.
* Pasting the value of a single select option into a single select field now selects the
  first option with that value.
* The API now returns appropriate errors when trying to create a field with a name which is too long.
* Importing table data with a column name that is too long will now truncate that name.
* Fixed error when rapidly switching between template tables or views in the template 
  preview.
* Upgraded Django to version 3.2.6 and also upgraded all other backend libraries to 
  their latest versions.
* Fix minor error that could sometimes occur when a row and it's table/group/database
  were deleted in rapid succession.
* Fix accidentally locking of too many rows in various tables during update operations.
* Introduced the has file type filter.
* Fixed bug where the backend would fail hard when an invalid integer was provided as
  'before_id' when moving a row by introducing a decorator to validate query parameters.
* Fixed bug where copying a cell containing a null value resulted in an error.
* Added "Multiple Select" field type.
* Fixed a bug where the currently selected view was not in the viewport of the parent.
* Fixed a bug where views context would not scroll down after a new view has been added.
* New templates:
    * Recipe Book
    * Healthcare Facility Management
    * Bucket List
    * Apartment Hunt
    * Holiday Shopping
    * Email Marketing Campaigns
    * Book Writing Guide
    * Home Inventory
    * Political Campaign Contributions
* Updated templates:
    * Blog Post Management
* Fixed a bug where the backend would fail hard when trying to order by field name without
  using `user_field_names`.
* Added "Formula" field type with 30+ useful functions allowing dynamic per row
  calculations.

## Released (2021-08-11)

* Made it possible to leave a group.
* Changed web-frontend `/api/docs` route into `/api-docs`.
* Bumped the dependencies.
* The internal setting allowing Baserow to run with the user tables in a separate 
  database has been removed entirely to prevent data integrity issues.
* Fixed bug where the currently selected dropdown item is out of view from the dropdown
  window when scrolling with the arrow keys.
* Introduced link row field has row filter.
* Made the form view compatible with importing and exporting.
* Made it possible to use the "F2"-Key to edit a cell without clearing the cell content.
* Added password validation to password reset page.
* Add backup and restore database management commands.
* Dropped the `old_name` column.
* Hide view types that can't be exported in the export modal.
* Relaxed the URL field validator and made it consistent between the backend and 
  web-frontend.
* Fixed nuxt not restarting correctly using the provided Baserow supervisor config file.
* Added steps on how to configure Baserow to send emails in the install-on-ubuntu guide.
* Enabled password validation in the backend.
* **Premium**: You can now comment and discuss rows with others in your group, click the
  expand row button at the start of the row to view and add comments.
* Added "Last Modified" and "Created On" field types.
* Fixed moment issue if core is installed as a dependency.
* New templates:
  * Blog Post Management
* Updated templates:
  * Personal Task Manager
  * Wedding Planning
  * Book Catalog
  * Applicant Tracker
  * Project Tracker
* Fixed earliest and latest date aggregations

## Released (2021-07-16)

* Fix bug preventing fields not being able to be converted to link row fields in some
  situations.

## Released (2021-07-15)

* **Breaking Change**: Baserow's `docker-compose.yml` no longer exposes ports for 
  the `db`, `mjml` and `redis` containers for security reasons. 
* **Breaking Change**: `docker-compose.yml` will by default only expose Baserow on 
  `localhost` and not `0.0.0.0`, meaning it will not be accessible remotely unless 
  manually configured.

## Released (2021-07-13)

* Added a Heroku template and one click deploy button.
* Fixed bug preventing the deletion of rows with a blank single select primary field.
* Fixed error in trash cleanup job when deleting multiple rows and a field from the
  same table at once.

## Released (2021-07-12)

* Made it possible to list table field meta-data with a token.
* Added form view.
* The API endpoint to update the grid view field options has been moved to
  `/api/database/views/{view_id}/field-options/`.
* The email field's validation is now consistent and much more permissive allowing most 
  values which look like email addresses.
* Add trash where deleted apps, groups, tables, fields and rows can be restored 
  deletion.
* Fix the create group invite endpoint failing when no message provided.
* Single select options can now be ordered by drag and drop. 
* Added before and after date filters.
* Support building Baserow out of the box on Ubuntu by lowering the required docker
  version to build Baserow down to 19.03.
* Disallow duplicate field names in the same table, blank field names or field names
  called 'order' and 'id'. Existing invalid field names will be fixed automatically. 
* Add user_field_names GET flag to various endpoints which switches the API to work
  using actual field names and not the internal field_1,field_2 etc identifiers.
* Added templates:
  * Commercial Property Management
  * Company Asset Tracker
  * Student Planner

## Released (2021-06-02)

* Fixed bug where the grid view would fail hard if a cell is selected and the component
  is destroyed.
* Made it possible to import a JSON file when creating a table.
* Made it possible to order the views by drag and drop.
* Made it possible to order the groups by drag and drop.
* Made it possible to order the applications by drag and drop.
* Made it possible to order the tables by drag and drop.
* **Premium**: Added an admin dashboard.
* **Premium**: Added group admin area allowing management of all baserow groups.
* Added today, this month and this year filter.
* Added a page containing external resources to the docs.
* Added a human-readable error message when a user tries to sign in with a deactivated
  account.
* Tables and views can now be exported to CSV (if you have installed using the ubuntu 
  guide please use the updated .conf files to enable this feature).
* **Premium** Tables and views can now be exported to JSON and XML.
* Removed URL field max length and fixed the backend failing hard because of that.
* Fixed bug where the focus of an Editable component was not always during and after
  editing if the parent component had overflow hidden.
* Fixed bug where the selected view would still be visible after deleting it.
* Templates:
  * Lightweight CRM
  * Wedding Planning
  * Book Catalog
  * App Pitch Planner

## Released (2021-05-11)

* Added configurable field limit.
* Fixed memory leak in the `link_row` field.
* Switch to using a celery based email backend by default.
* Added `--add-columns` flag to the `fill_table` management command. It creates all the
  field types before filling the table with random data.
* Reworked Baserow's Docker setup to be easier to use, faster to build and more secure.
* Make the view header more compact when the content doesn't fit anymore.
* Allow providing a `template_id` when registering a new account, which will install
  that template instead of the default database.
* Made it possible to drag and drop rows in the desired order.
* Fixed bug where the rows could get out of sync during real time collaboration.
* Made it possible to export and import the file field including contents.
* Added `fill_users` admin management command which fills baserow with fake users.
* Made it possible to drag and drop the views in the desired order.
* **Premium**: Added user admin area allowing management of all baserow users.

## Released (2021-04-08)

* Added support for importing tables from XML files.
* Added support for different** character encodings when importing CSV files.
* Prevent websocket reconnect loop when the authentication fails.
* Refactored the GridView component and improved interface speed.
* Prevent websocket reconnect when the connection closes without error.
* Added gunicorn worker test to the CI pipeline.
* Made it possible to re-order fields in a grid view.
* Show the number of filters and sorts active in the header of a grid view.
* The first user to sign-up after installation now gets given staff status.
* Rename the "includes" get parameter across all API endpoints to "include" to be 
  consistent.
* Add missing include query parameter and corresponding response attributes to API docs. 
* Remove incorrectly included "filters_disabled" field from 
  list_database_table_grid_view_rows api endpoint.
* Show an error to the user when the web socket connection could not be made and the
  reconnect loop stops.
* Fixed 100X backend web socket errors when refreshing the page.
* Fixed SSRF bug in the file upload by URL by blocking urls to the private network.
* Fixed bug where an invalid date could be converted to 0001-01-01.
* The list_database_table_rows search query parameter now searches all possible field
  types.
* Add Phone Number field.
* Add support for Date, Number and Single Select fields to the Contains and Not Contains
  view 
  filters.
* Searching all rows can now be done by clicking the new search icon in the top right.

## Released (2021-03-01)

* Redesigned the left sidebar.
* Fixed error when a very long user file name is provided when uploading.
* Upgraded DRF Spectacular dependency to the latest version.
* Added single select field form option validation.
* Changed all cookies to SameSite=lax.
* Fixed the "Ignored attempt to cancel a touchmove" error.
* Refactored the has_user everywhere such that the raise_error argument is used when
  possible.
* Added Baserow Cloudron app.
* Fixed bug where a single select field without options could not be converted to a
  another field.
* Fixed bug where the Editable component was not working if a prent a user-select:
  none; property.
* Fail hard when the web-frontend can't reach the backend because of a network error.
* Use UTC time in the date picker.
* Refactored handler get_* methods so that they never check for permissions.
* Made it possible to configure SMTP settings via environment variables.
* Added field name to the public REST API docs.
* Made the public REST API docs compatible with smaller screens.
* Made it possible for the admin to disable new signups.
* Reduced the amount of queries when using the link row field.
* Respect the date format when converting to a date field.
* Added a field type filename contains filter.

## Released (2021-02-04)

* Upgraded web-frontend dependencies.
* Fixed bug where you could not convert an existing field to a single select field
  without select options.
* Fixed bug where is was not possible to create a relation to a table that has a single
  select as primary field.
* Implemented real time collaboration.
* Added option to hide fields in a grid view.
* Keep token usage details.
* Fixed bug where an incompatible row value was visible and used while changing the
  field type.
* Fixed bug where the row in the RowEditModel was not entirely reactive and wouldn't be
  updated when the grid view was refreshed.
* Made it possible to invite other users to a group.

## Released (2021-01-06)

* Allow larger values for the number field and improved the validation.
* Fixed bug where if you have no filters, but the filter type is set to `OR` it always
  results in a not matching row state in the web-frontend.
* Fixed bug where the arrow navigation didn't work for the dropdown component in
  combination with a search query.
* Fixed bug where the page refreshes if you press enter in an input in the row modal.
* Added filtering by GET parameter to the rows listing endpoint.
* Fixed drifting context menu.
* Store updated and created timestamp for the groups, applications, tables, views,
  fields and rows.
* Made the file name editable.
* Made the rows orderable and added the ability to insert a row at a given position.
* Made it possible to include or exclude specific fields when listing rows via the API.
* Implemented a single select field.
* Fixed bug where inserting above or below a row created upon signup doesn't work
  correctly.

## Released (2020-12-01)

* Added select_for_update where it was still missing.
* Fixed API docs scrollbar size issue.
* Also lint the backend tests.
* Implemented a switch to disable all filters without deleting them.
* Made it possible to order by fields via the rows listing endpoint.
* Added community chat to the readme.
* Made the cookies strict and secure.
* Removed the redundant _DOMAIN variables.
* Set un-secure lax cookie when public web frontend url isn't over a secure connection.
* Fixed bug where the sort choose field item didn't have a hover effect.
* Implemented a file field and user files upload.
* Made it impossible for the `link_row` field to be a primary field because that can
  cause the primary field to be deleted.

## Released (2020-11-02)

* Highlight the row of a selected cell.
* Fixed error when there is no view.
* Added Ubuntu installation guide documentation.
* Added Email field.
* Added importer abstraction including a CSV and tabular paste importer.
* Added ability to navigate dropdown menus with arrow keys.
* Added confirmation modals when the user wants to delete a group, application, table,
  view or field.
* Fixed bug in the web-frontend URL validation where a '*' was invalidates.
* Made it possible to publicly expose the table data via a REST API.

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
