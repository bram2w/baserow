# Changelog

## Released (2023-01-18_1.14.0)

### New features
* When your permissions change you now get notified in the frontend to reload your page [#1312](https://gitlab.com/bramw/baserow/-/issues/1312)
* Add "has" and "has not" filters for Collaborators field. [#1204](https://gitlab.com/bramw/baserow/-/issues/1204)
* Database and table ids are now hashed in websocket messages to not leak sensitive data [#1374](https://gitlab.com/bramw/baserow/-/issues/1374)
* Added a new setting to the Admin Settings page to enable/disable global group creation. [#1311](https://gitlab.com/bramw/baserow/-/issues/1311)
* Select the primary field in the grid view after creating a new row. [#1217](https://gitlab.com/bramw/baserow/-/issues/1217)
* Limit the amount of characters for messages supplied with group invitations to 250 [#1455](https://gitlab.com/bramw/baserow/-/issues/1455)
* Pressing shift + enter in a selected cell of the grid view creates a new row. [#1208](https://gitlab.com/bramw/baserow/-/issues/1208)
* Pressing enter on a selected cell should select the cell below. [#1329](https://gitlab.com/bramw/baserow/-/issues/1329)
* ./dev.sh now uses "docker compose" command if available.
* Add the "Audit Log" enterprise feature. Now admins can see every action that has been done in the instance. [#1152](https://gitlab.com/bramw/baserow/-/issues/1152)
* New templates:
  * Car Dealership Inventory
  * Car Dealership Services
  * Customer Research
  * Frequent Flyer Rewards
  * Grocery Planner
* Introduced a "select" and "deselect all" members button to the teams modal. [#1335](https://gitlab.com/bramw/baserow/-/issues/1335)
* Add various help icons to explain RBAC in the UI [#1318](https://gitlab.com/bramw/baserow/-/issues/1318)
* Add Free label to free roles on role selector [#1504](https://gitlab.com/bramw/baserow/-/issues/1504)

### Bug fixes
* Fixed encoding issue where you couldn't import xml files with non-ascii characters [#1360](https://gitlab.com/bramw/baserow/-/issues/1360)
* Resolved an issue in `delete_expired_users` so that it doesn't delete groups when admins are deactivated and not marked for deletion. [#1503](https://gitlab.com/bramw/baserow/-/issues/1503)
* Fixed a typo in the docker-compose.no-caddy.yml so it works out of the box. [#1469](https://gitlab.com/bramw/baserow/-/issues/1469)
* Tweaked the curl examples in the API documentation so that they work properly in all $SHELLs. [#1462](https://gitlab.com/bramw/baserow/-/issues/1462)
* Fixed bug where it was not possible to change `conditional_color` decorator provider color after reloading. [#1098](https://gitlab.com/bramw/baserow/-/issues/1098)
* Fixed Change Password dialog not visible. [#1501](https://gitlab.com/bramw/baserow/-/issues/1501)
* Replaced the "contains not" and "has not" English filters with "doesn't contain" and "doesn't have" respectively. [#1452](https://gitlab.com/bramw/baserow/-/issues/1452)
* Prevent errors after migrating and syncing RBAC roles by adding migration to rename NO_ROLE to NO_ACCESS [#1478](https://gitlab.com/bramw/baserow/-/issues/1478)
* Fixed HOURS_UNTIL_TRASH_PERMANENTLY_DELETED environment variable is not converted to int. [#1499](https://gitlab.com/bramw/baserow/-/issues/1499)
* Fixed bug preventing groups from being restored when RBAC was enabled [#1485](https://gitlab.com/bramw/baserow/-/issues/1485)
* Fixed issue where 2 admins could lower each others permissions at the same time and lock each other out [#1443](https://gitlab.com/bramw/baserow/-/issues/1443)
* Fixed issue where importing a database would immediately close the modal and not show progress [#1492](https://gitlab.com/bramw/baserow/-/issues/1492)
* Fixed issue during importing of serialized applications causing formula columns to have incorrect database column [#1220](https://gitlab.com/bramw/baserow/-/issues/1220)
* Form validator shows the correct message when a field is required. [#1475](https://gitlab.com/bramw/baserow/-/issues/1475)
* Fixed upgrading a license from premium to enterprise results in an expired license. [#1403](https://gitlab.com/bramw/baserow/-/issues/1403)

### Refactors
* Replaced deprecated `execCommand('copy')` with `clipboard API` for copy and paste. [#1392](https://gitlab.com/bramw/baserow/-/issues/1392)
* Refactor paving the way for a future removal of the `ExportJob` system in favor of the `core/jobs` one.
* Introduce a single-parent hierarchy for models.

### Breaking API changes
* Changed the return code from `HTTP_200_OK` to `HTTP_202_ACCEPTED` if a `POST` is submitted to `/api/snapshots/application/$ID/` to start the async job.


## Released (2022-12-22_1.13.3)

### New features
* Users with roles higher than viewer on tables and databases now counted as paid users
on the enterprise plan including users who get those roles from a team. [#1322](https://gitlab.com/bramw/baserow/-/issues/1322)
* Added more Maths formula functions. [#1183](https://gitlab.com/bramw/baserow/-/issues/1183)
* Possibility to disable password authentication if another authentication provider is enabled. [#1317](https://gitlab.com/bramw/baserow/-/issues/1317)
* Add support for wildcard '*' in the FEATURE_FLAG env variable which enables all features.
* The ordering APIs can now accept a partial list of ids to order only these ids.
* (Enterprise Preview Feature) Database and Table level RBAC with Teams are now available as a preview feature for enterprise users, Add 'RBAC' to the FEATURE_FLAG env and restart var to enable.
* Add support for "Empty" and "Not Empty" filters for Collaborator field. [#1205](https://gitlab.com/bramw/baserow/-/issues/1205)

### Bug fixes
* Fixed an issue where you would get an error if you accepted a group invitation with `NO_ACCESS` as you role [#1394](https://gitlab.com/bramw/baserow/-/issues/1394)
* Use the correct `OperationType` to restore rows [#1389](https://gitlab.com/bramw/baserow/-/issues/1389)
* Prevent zooming in when clicking on an input on mobile. [#722](https://gitlab.com/bramw/baserow/-/issues/722)
* Link/Lookup/Formula fields work again when restricting a users access to the related table [#1439](https://gitlab.com/bramw/baserow/-/issues/1439)

### Refactors
* Set a fixed width for `card_cover` thumbnails to have better-quality images. [#1278](https://gitlab.com/bramw/baserow/-/issues/1278)


## Released (2022-12-8_1.13.2)

### New features
* Automatically enable/disable enterprise features upon activation/deactivation without needing a page refresh first. [#1306](https://gitlab.com/bramw/baserow/-/issues/1306)
* Don't require password verification when deleting user account. [#1401](https://gitlab.com/bramw/baserow/-/issues/1401)
* Improved grid view on smaller screens by not making the primary field sticky. [#690](https://gitlab.com/bramw/baserow/-/issues/690)
* Add drag and drop zone for files to the row edit modal [#1161](https://gitlab.com/bramw/baserow/-/issues/1161)
* Added the teams functionality as an enterprise feature. [#1226](https://gitlab.com/bramw/baserow/-/issues/1226)
* New items automatically get a new name in the modal. [1166](https://gitlab.com/bramw/baserow/-/issues/1166)
* Allow creating a new option by pressing enter in the dropdown [#1169](https://gitlab.com/bramw/baserow/-/issues/1169)

### Bug fixes
* Fixed failing webhook call log creation when a table has more than one webhooks. [#1100](https://gitlab.com/bramw/baserow/-/issues/1100)
* Fix "ERR_REDIRECT" for authenticated users redirected to the dashboard from the signup page. [1125](https://gitlab.com/bramw/baserow/-/issues/1125)
* Fixed bug where only one condition per field was working in form's views. [#1400](https://gitlab.com/bramw/baserow/-/issues/1400)
* Fixed the Heroku deployment template. [#1420](https://gitlab.com/bramw/baserow/-/issues/1420)
* Fixed a problem of some specific error messages not being recognized by the web front-end.

### Refactors
* Refresh the JWT token when needed instead of periodically. [#1294](https://gitlab.com/bramw/baserow/-/issues/1294)
* Remove "// Baserow" from title on a publicly shared view if `show_logo` is set to false. [#1378](https://gitlab.com/bramw/baserow/-/issues/1378)


## Released (2022-11-22_1.13.1)

### New features
* OAuth 2 flows now support redirects to specific pages. [#1288](https://gitlab.com/bramw/baserow/-/issues/1288)
* Implemented the option to start direct support if the instance is on the enterprise plan.
* Made it possible to optionally hide fields in a publicly shared form by providing the `hide_FIELD` query parameter. [#1096](https://gitlab.com/bramw/baserow/-/issues/1096)
* Add support for language selection and group invitation tokens for OAuth 2 and SAML. [#1293](https://gitlab.com/bramw/baserow/-/issues/1293)
* Calendar / date field picker: Highlight the current date and weekend [#1128](https://gitlab.com/bramw/baserow/-/issues/1128)

### Bug fixes
* `permanently_delete_marked_trash` task no longer fails on permanently deleting a table before an associated rows batch. [#1266](https://gitlab.com/bramw/baserow/-/issues/1266)
* Fixed bug where "add filter" link was not clickable if the primary field has no compatible filter types. [#1302](https://gitlab.com/bramw/baserow/-/issues/1302)
* Fixed authenticated state changing before redirected to the login page when logging off. [#1328](https://gitlab.com/bramw/baserow/-/issues/1328)
* Standardize the API documentation "token" references.
* Fixed OAuth 2 flows for providers that don't provide user's name. Email will be used as a temporary placeholder so that an account can be created. [#1371](https://gitlab.com/bramw/baserow/-/issues/1371)
* Raise an exception when a user doesn't have a required feature on an endpoint

### Refactors
* Moved the Open Sans font to the static directory instead of a Google fonts dependency. [#1246](https://gitlab.com/bramw/baserow/-/issues/1246)
* Replace the CSS classes for SSO settings forms. [#1336](https://gitlab.com/bramw/baserow/-/issues/1336)
* Changed `TableGroupStorageUsageItemType.calculate_storage_usage` to use a PL/pgSQL function to speedup the storage usage calculation.


## Released (2022-11-02_1.13.0)

### New features
* Added OAuth2 support for Single Sign On with Google, Facebook, GitHub, and GitLab as preconfigured providers. Added general support for OpenID Connect. [#1254](https://gitlab.com/bramw/baserow/-/issues/1254)
* Made it possible to filter on the `created_on` and `updated_on` columns, even though
they're not exposed via fields.
* Added the ability to double click a grid field name so that quick edits can be made. [#1147](https://gitlab.com/bramw/baserow/-/issues/1147)
* Add an option to remove the Baserow logo from your public view. [#1203](https://gitlab.com/bramw/baserow/-/issues/1203)
* Always allow the cover image of a gallery view to be accessible by a public view [#1113](https://gitlab.com/bramw/baserow/-/issues/1113)
* Made it possible to add additional signup step via plugins.
* Upgraded docker containers base images from `debian:buster-slim` to the latest stable `debian:bullseye-slim`.
* Expose `read_only` in the list fields endpoint.
* Added Zapier integration code. [#816](https://gitlab.com/bramw/baserow/-/issues/816)
* Added SAML protocol implementation for Single Sign On as an enterprise feature. [#1227](https://gitlab.com/bramw/baserow/-/issues/1227)
* Upgraded python version from `python-3.7.16` to `python-3.9.2`.
* Background pending tasks like duplication and template_install are restored in a new frontend session if unfinished. [#885](https://gitlab.com/bramw/baserow/-/issues/885)

### Bug fixes
* Fixed slug rotation for GalleryView. [#1232](https://gitlab.com/bramw/baserow/-/issues/1232)
* Fixed bug where the row metadata was not updated when receiving a realtime event.
* Duplicating a table with a removed single select option value no longer results in an error. [#1263](https://gitlab.com/bramw/baserow/-/issues/1263)
* Fixed bug where it was not possible to select text in a selected and editing cell in Chrome. [#1234](https://gitlab.com/bramw/baserow/-/issues/1234)
* Selecting text in models, contexts, form fields and grid view cells no longer unselects when releasing the mouse outside. [#1243](https://gitlab.com/bramw/baserow/-/issues/1243)

### Refactors
* Changed the add label of several buttons.
* Frontend now install templates as an async job in background instead of using a blocking call. [#885](https://gitlab.com/bramw/baserow/-/issues/885)
* Replace members modal with a new settings page. [#1229](https://gitlab.com/bramw/baserow/-/issues/1229)

### Breaking API changes
* Changed the JWT library to fix a problem causing the refresh-tokens not working properly. [#787](https://gitlab.com/bramw/baserow/-/issues/787)
* The "token_auth" endpoint response and "user_data_updated" messages now have an "active_licenses" key instead of "premium" indicating what licenses the user has active. [#1230](https://gitlab.com/bramw/baserow/-/issues/1230)
* List jobs endpoint "list_job" returns now an object with jobs instead of a list of jobs. [#885](https://gitlab.com/bramw/baserow/-/issues/885)
* Changed error codes returned by the premium license API endpoints to replacing `PREMIUM_LICENSE` with `LICENSE`. [#1230](https://gitlab.com/bramw/baserow/-/issues/1230)


## Released (2022-09-20_1.12.1)

### New features
* Updated templates:
  * Benefit Show Manager
  * Car Hunt
  * Wedding Client Planner
* Always allow the cover image of a gallery view to be accessible by a public view [#1113](https://gitlab.com/bramw/baserow/-/issues/1113)
* Made it possible to share the Kanban view publicly. [#1146](https://gitlab.com/bramw/baserow/-/issues/1146)
* Added link, button, get_link_label and get_link_url formula functions. [#818](https://gitlab.com/bramw/baserow/-/issues/818)
* New templates:
  * Copy Management
  * Hiking Guide
  * New Hire Onboarding
  * Property Showings
  * QA Test Scripts
  * Risk Assessment and Management
  * Web App UAT
* Add env vars for controlling which URLs and IPs webhooks are allowed to use. [#931](https://gitlab.com/bramw/baserow/-/issues/931)
* Add a rich preview while importing data to an existing table. [#1120](https://gitlab.com/bramw/baserow/-/issues/1120)
* Show database and table duplication progress in the left sidebar. [#1059](https://gitlab.com/bramw/baserow/-/issues/1059)
* Added support for placeholders in form headings and fields. [#1168](https://gitlab.com/bramw/baserow/-/issues/1168)

### Bug fixes
* Fixed a bug that breaks the link row modal when a formula is referencing a single select field. [#1111](https://gitlab.com/bramw/baserow/-/issues/1111)
* Fixed Multiple Collaborators field renames. Now renaming the field won't recreate the field so that data is preserved.
* Always allow the cover image of a gallery view to be accessible by a public view [#1113](https://gitlab.com/bramw/baserow/-/issues/1113)
* Static files collected from plugins will now be correctly served.
* Fixed an issue where customers with malformed file extensions were unable to snapshot or duplicate properly [#1194](https://gitlab.com/bramw/baserow/-/issues/1194)
* Plugins can now change any and all Django settings instead of just the ones set previously by Baserow.
* The /admin url postfix will now be passed through to the backend API for plugins to use.

### Refactors
* Formulas which referenced other aggregate formulas now will work correctly. [#1081](https://gitlab.com/bramw/baserow/-/issues/1081)
* Improved file import UX for existing table. [#1120](https://gitlab.com/bramw/baserow/-/issues/1120)
* Used SimpleGrid component for SelectRowModal. [#1120](https://gitlab.com/bramw/baserow/-/issues/1120)


## Released (2022-09-07_1.12.0)

### New features
* New signals `user_updated`, `user_deleted`, `user_restored`, `user_permanently_deleted` were added to track user changes.
* Only allow relative urls in the in the original query parameter.
* Add cancel button to field update context [#1020](https://gitlab.com/bramw/baserow/-/issues/1020)
* Add API token authentication support to multipart and via-URL file uploads. [#255](https://gitlab.com/bramw/baserow/-/issues/255)
* Enable `file field` in `form` views. [#525](https://gitlab.com/bramw/baserow/-/issues/525)
* Force browser language when viewing a public view. [#834](https://gitlab.com/bramw/baserow/-/issues/834)
* `list_groups` endpoint now also returns the list of all group users for each group.
* Search automatically after 400ms when chosing a related field via the modal. [#1091](https://gitlab.com/bramw/baserow/-/issues/1091)
* Add row url parameter to `gallery` and `kanban` view.
* Added missing success printouts to `count_rows` and `calculate_storage_usage` commands.
* Add a tooltip to applications and tables in the left sidebar to show the full name. [#986](https://gitlab.com/bramw/baserow/-/issues/986)
* Introduced a premium form survey style theme. [#524](https://gitlab.com/bramw/baserow/-/issues/524)
* Add `isort` settings to sort python imports.
* Fields can now be duplicated with their cell values also. [#964](https://gitlab.com/bramw/baserow/-/issues/964)
* Added Multiple Collaborators field type. [#1119](https://gitlab.com/bramw/baserow/-/issues/1119)
* Allow creating new rows when selecting a related row [#1064](https://gitlab.com/bramw/baserow/-/issues/1064)
* Allow not creating a reversed relationship with the link row field. [#1063](https://gitlab.com/bramw/baserow/-/issues/1063)
* Add navigation buttons to the `RowEditModal`.
* Sort fields on row select modal by the order of the first view in the related table. [#1062](https://gitlab.com/bramw/baserow/-/issues/1062)

### Bug fixes
* Fixed horizontal scroll on Mac OSX.
* "Link to table" field does not allow submitting empty values. [#1159](https://gitlab.com/bramw/baserow/-/issues/1159)
* Fixed bug where the link row field lookup didn't work in combination with password
protected views.
* Resolve circular dependency in `FieldWithFiltersAndSortsSerializer` [#1113](https://gitlab.com/bramw/baserow/-/issues/1113)
* Prefetch field options on views that are iterated over on field update realtime events [#1113](https://gitlab.com/bramw/baserow/-/issues/1113)
* Clearing cell values multi-selected from right to left with backspace shifts selection to the right and results in wrong deletion. [#1134](https://gitlab.com/bramw/baserow/-/issues/1134)
* Fixed bug where the row coloring didn't work in combination with group level premium.
* Fixed bug where the "Create option" button was not visible for the single and multiple
select fields in the row edit modal.
* Fixed a bug that prevent to use arrows keys in the grid view when a formula field is selected. [#1136](https://gitlab.com/bramw/baserow/-/issues/1136)
* Fixed a bug when importing Airtable base with a date field less than 1000. [#1046](https://gitlab.com/bramw/baserow/-/issues/1046)
* Fixed broken call grouping when getting linked row names from server.
* Fixed a bug that make the grid view crash when searching text and a formula field is referencing a singe-select field. [#1110](https://gitlab.com/bramw/baserow/-/issues/1110)
* Add new filter types 'is after today' and 'is before today'. [#1093](https://gitlab.com/bramw/baserow/-/issues/1093)
* Fix various misspellings. Contributed by [@Josh Soref](https://github.com/jsoref/) using [check-spelling.dev](https://check-spelling.dev/)
* Resolve an invalid URL in the "Backend URL mis-configuration detected" error message. [#967](https://gitlab.com/bramw/baserow/-/issues/967)
* Resolve an issue with uploading a file via a URL when it contains a querystring. [#1034](https://gitlab.com/bramw/baserow/-/issues/1034)

### Refactors
* Make it possible to copy/paste/import from/to text values for multi-select and file fields. [#913](https://gitlab.com/bramw/baserow/-/issues/913)
* Fixed crash in gallery view with searching. [#1130](https://gitlab.com/bramw/baserow/-/issues/1130)
* Fix view and fields getting out of date on realtime updates. [#1112](https://gitlab.com/bramw/baserow/-/issues/1112)
* Users can copy/paste images into a file field. [#367](https://gitlab.com/bramw/baserow/-/issues/367)
* Fixed error when sharing a view publicly with sorts more than one multi-select field. [#1082](https://gitlab.com/bramw/baserow/-/issues/1082)

### Breaking API changes
* The date parsing takes the date format into account when parsing unless the format respect the ISO-8601 format. This will change the value for ambiguous dates like `02/03/2020`.
* The export format of file fields has changed for CSV files. The new format is `fileName1.ext (file1url),fileName2.ext (file2url), ...`.


## Released (2022-07-27_1.11.0)

### New features
* Applications can now be duplicated. [#960](https://gitlab.com/bramw/baserow/-/issues/960)
* Added option to use view's filters and sorting when listing rows. [#190](https://gitlab.com/bramw/baserow/-/issues/190)
* Allow users to use row id in the form redirect URL. [#871](https://gitlab.com/bramw/baserow/-/issues/871)
* Added public gallery view [#1057](https://gitlab.com/bramw/baserow/-/issues/1057)
* When viewing an expanded row switch to a unique URL which links to that row. [#938](https://gitlab.com/bramw/baserow/-/issues/938)
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
* Added a new "is months ago filter". [#1018](https://gitlab.com/bramw/baserow/-/issues/1018)
* Fixed bug with 404 middleware returning different 404 error messages based on the endpoint.
* Made it possible to import data into an existing table. [#342](https://gitlab.com/bramw/baserow/-/issues/342)
* Added a new `ClientUndoRedoActionGroupId` request header to bundle multiple actions in a single API call. [#951](https://gitlab.com/bramw/baserow/-/issues/951)
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
* Tables can now be duplicated. [#961](https://gitlab.com/bramw/baserow/-/issues/961)
* Introduced environment variable to disable Google docs file preview. [#1074](https://gitlab.com/bramw/baserow/-/issues/1074)
* Show badge when the user has account level premium.
* Added `in this week` filter [#954](https://gitlab.com/bramw/baserow/-/issues/954)
* Conditionally show form fields.
* Made it possible to select the entire row via the row context menu. [#1061](https://gitlab.com/bramw/baserow/-/issues/1061)
* Show modal when the users clicks on a deactivated premium features. [#1066](https://gitlab.com/bramw/baserow/-/issues/1066)
* Replaced all custom alert code with `Alert` component [#1016](https://gitlab.com/bramw/baserow/-/issues/1016)
* Add ability to create and restore snapshots. [#141](https://gitlab.com/bramw/baserow/-/issues/141)
* Added a new "is years ago filter". [#1019](https://gitlab.com/bramw/baserow/-/issues/1019)
* Add configs and docs for VSCode setup. [#854](https://gitlab.com/bramw/baserow/-/issues/854)

### Bug fixes
* Ensure the latest error is always shown when clicking the formula refresh options link. [#1092](https://gitlab.com/bramw/baserow/-/issues/1092)
* Fix the perm delete trash cleanup job failing for self linking tables. [#1075](https://gitlab.com/bramw/baserow/-/issues/1075)
* Fixed problem when new webhooks would be sent twice with both old and new payload.
* Upgrade the images provided in our example docker-compose files to be the latest and most secure. [#1056](https://gitlab.com/bramw/baserow/-/issues/1056)
* Fixed problem causing kanban view duplication to fail silently. [#1109](https://gitlab.com/bramw/baserow/-/issues/1109)
* Fixed changing field type to unsupported form view bug. [#1078](https://gitlab.com/bramw/baserow/-/issues/1078)
* Fixed duplicating view with that depends on select options mapping. [#1104](https://gitlab.com/bramw/baserow/-/issues/1104)
* Display round and trunc functions in the formula edit modal, rename int to trunc and make these functions handle weird inputs better. [#1095](https://gitlab.com/bramw/baserow/-/issues/1095)
* Fix backspace and delete keys breaking after selecting a formula text cell. [#1085](https://gitlab.com/bramw/baserow/-/issues/1085)
* Don't allow invalid aggregate formulas from being created causing errors when inserting rows. [#1089](https://gitlab.com/bramw/baserow/-/issues/1089)
* Disable table import field type guessing and instead always import as text fields. [#1050](https://gitlab.com/bramw/baserow/-/issues/1050)
* Fix some rare errors when combining the if and divide formula functions. [#1086](https://gitlab.com/bramw/baserow/-/issues/1086)
* Add better error handling to row count job. [#1051](https://gitlab.com/bramw/baserow/-/issues/1051)

### Breaking API changes
* **breaking change** Webhooks `row.created`, `row.updated` and `row.deleted` are
replaced with `rows.created`, `rows.updated` and `rows.deleted`, containing multiple
changed rows at once. Already created webhooks will still be called, but the received
body will contain only the first changed row instead of all rows. It is highly
recommended to convert all webhooks to the new types.
* Fix not being able to paste multiple cells when a formula field of array or single select type was in an error state. [#1084](https://gitlab.com/bramw/baserow/-/issues/1084)
* Concurrent field updates will now respond with a 409 instead of blocking until the previous update finished, set the env var BASEROW_WAIT_INSTEAD_OF_409_CONFLICT_ERROR to revert to the old behaviour. [#1097](https://gitlab.com/bramw/baserow/-/issues/1097)
* API endpoint `/database/views/grid/${viewSlug}/public/info/` has been replaced by `/database/views/${viewSlug}/public/info/` [#1057](https://gitlab.com/bramw/baserow/-/issues/1057)
* Removed `primary` from all `components`and `stores` where it isn't absolutely required. [#1057](https://gitlab.com/bramw/baserow/-/issues/1057)
* API endpoints `undo` and `redo` now returns a list of actions undone/redone instead of a single action.


## Released (2022-07-05_1.10.2)

### New features
* Add the ability to disable the model cache with the new BASEROW_DISABLE_MODEL_CACHE env variable.
* Made it clearer that you're navigating to baserow.io when clicking the "Get a license"
button.
* Added new `group_user_added` signal that is called when an user accept an invitation to join a group.
* Add startup check ensuring BASEROW_PUBLIC_URL and related variables are correct. [#1041](https://gitlab.com/bramw/baserow/-/issues/1041)
* Add basic field duplication. [#964](https://gitlab.com/bramw/baserow/-/issues/964)
* Redirect to signup instead of the login page if there are no admin users. [#1035](https://gitlab.com/bramw/baserow/-/issues/1035)
* Add support for horizontal scrolling in grid views pressing Shift + mouse-wheel. [#867](https://gitlab.com/bramw/baserow/-/issues/867)
* Link to table field can now link rows in the same table. [#798](https://gitlab.com/bramw/baserow/-/issues/798)
* Made it possible to extend the register page.
* Views can be duplicated. [#962](https://gitlab.com/bramw/baserow/-/issues/962)
* Added prefill query parameters for forms. [#852](https://gitlab.com/bramw/baserow/-/issues/852)
* Added multi-cell clearing via backspace key (delete on Mac).
* Made it possible to extend the app layout.
* Added Link Row contains filter. [874](https://gitlab.com/bramw/baserow/-/issues/874)
* Added API exception registry that allows plugins to provide custom exception mappings for the REST API.
* Added new `before_group_deleted` signal that is called just before a group would end up in the trash.
* Added formula round and int functions. [#891](https://gitlab.com/bramw/baserow/-/issues/891)
* `./dev.sh all_in_one_dev` now starts a hot reloading dev mode using the all-in-one image.
* Added possibility to delete own user account [#880](https://gitlab.com/bramw/baserow/-/issues/880)
* Made the styling of the dashboard cleaner and more efficient. [#1023](https://gitlab.com/bramw/baserow/-/issues/1023)
* Allow to import more than 15Mb. [949](ttps://gitlab.com/bramw/baserow/-/issues/949)

### Bug fixes
* Fix errors when using row_id formula function with left/right functions.
* Fix views becoming inaccessible due to race condition when invalidating model cache. [#1040](https://gitlab.com/bramw/baserow/-/issues/1040)
* Fix dependant fields not being updated if the other side of a link row field changed. [918](https://gitlab.com/bramw/baserow/-/issues/918)
* Upload modal no longer closes when removing a file. [#569](https://gitlab.com/bramw/baserow/-/issues/569)
* Fix lookup field conversions deleting all of its old field dependencies. [#1036](https://gitlab.com/bramw/baserow/-/issues/1036)
* API returns a nicer error if URL trailing slash is missing. [798](https://gitlab.com/bramw/baserow/-/issues/798)
* Fix nested aggregate formulas not calculating results or causing errors. [683](https://gitlab.com/bramw/baserow/-/issues/683)
* Fix get_human_readable_value crashing for some formula types. [#1042](https://gitlab.com/bramw/baserow/-/issues/1042)
* Fix regex_replace formula function allowing invalid types as params. [#1024](https://gitlab.com/bramw/baserow/-/issues/1024)
* Fix import form that gets stuck in a spinning state when it hits an error.
* Fix refresh formula options button always being shown initially. [#1037](https://gitlab.com/bramw/baserow/-/issues/1037)
* Fix rare formula bug with multiple different formulas and view filters in one table. [#801](https://gitlab.com/bramw/baserow/-/issues/801)
* Fix formula bugs caused by unsupported generation of BC dates. [#952](https://gitlab.com/bramw/baserow/-/issues/952)
* Fix converting a link row not updating dependants on the reverse side. [#1026](https://gitlab.com/bramw/baserow/-/issues/1026)
* Fix formula bug caused when looking up date intervals. [#924](https://gitlab.com/bramw/baserow/-/issues/924)
* Fix newly imported templates missing field dependencies for some link row fields. [#1025](https://gitlab.com/bramw/baserow/-/issues/1025)
* Add debugging commands/options for inspecting tables and updating formulas.
* Treat null values as zeros for numeric formulas. [#886](https://gitlab.com/bramw/baserow/-/issues/886)
* Fixed URL fields not being available in lookup fields. [#984](https://gitlab.com/bramw/baserow/-/issues/984)
* Added FormulaField to the options for the primary field. [#859](https://gitlab.com/bramw/baserow/-/issues/859)


## Released (2022-06-09_1.10.1)

### New features
* Formulas of type text now use textarea to show the cell value.
* Added multi-row delete.
* Fix formula bug caused when arguments of `when_empty` have different types.
* **breaking change** The API endpoint `/api/templates/install/<group_id>/<template_id>/`
is now a POST request instead of GET.
* Deprecate the SYNC_TEMPLATES_ON_STARTUP environment variable and no longer call the
sync_templates command on startup in the docker images.
* Added the ability to use commas as separators in number fields
* Fixed CSV import adding an extra row with field names if the no headers option is selected.
* Make fields sortable in row create/edit modal.
* Fix a bug in public grid views that prevented expanding long-text cells.
* Fixed bad request displayed with webhook endpoints that redirects
* Duplicate row.
* Added an admin setting to disable the ability to reset a users password.
* Added a dropdown to the grid view that allows you to
select the type of row identifier displayed next to a row (`Count`or `Row Identifier`).
* Plugins can now include their own menu or other template in the main menu sidebar.
* Shift+Enter on grid view go to field below
* Fix deadlocks and performance problems caused by un-needed accidental row locks.
* Added row coloring for Kanban and Gallery views
* Shift+Enter on grid view exit from editing mode for long text field
* Added BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION environment variable and now
do the sync_templates task in the background after migration to massively speedup
first time Baserow startup speed.


## Released (2022-10-05_1.10.0)

### New features
* Added undo/redo.
* Fix formula autocomplete for fields with multiple quotes
* **breaking change** The API endpoint `/api/database/formula/<field_id>/type/` now requires
`table_id` instead of `field_id`, and also `name` in the request body.
* Added a new BASEROW_EXTRA_ALLOWED_HOSTS optional comma separated environment variable
for configuring ALLOWED_HOSTS.
* Added new endpoint to get all configured aggregations for a grid view
* Pin backend python dependencies using pip-tools.
* Added new environment variable BASEROW_FILE_UPLOAD_SIZE_LIMIT_MB
* Fixed DONT_UPDATE_FORMULAS_AFTER_MIGRATION env var not working correctly.
* Fixed the unchecked percent aggregation calculation
* Add loading bar when syncing templates to make it obvious Baserow is still loading.
* Improved backup_baserow splitting multiselect through tables in separate batches.
* Fixed a bug where making a multiple cell selection starting from an
empty `link_row` or `formula` field was not possible in Firefox.
* Allow the setting of max request page size via environment variable.
* Raise Airtable import task error and fixed a couple of minor import bugs.
* Prevent the Airtable import from failing hard when an invalid date is provided.
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
* Scroll to the first error message if the form submission fail
* Fixed bug preventing file uploads via an url for self-hosters
* Fixed translations in emails sent by Baserow.
* Added select option suggestions when converting to a select field.
* Added password protection for publicly shared grids and forms.
* Made views trashable.
* Fixed occasional UnpicklingError error when getting a value from the model cache.
* Fixed a bug for some number filters that causes all rows to be returned when text is entered.
* Fix slowdown in large Baserow instances as the generated model cache got large.
* Fixed a bug that made it possible to delete created on/modified by fields on the web frontend.
* Shared public forms now don't allow creating new options
for single and multiple select fields.
* Stopped the generated model cache clear operation also deleting all other redis keys.
* Fixed the reactivity of the row values of newly created fields in some cases.
* Boolean field converts the word `checked` to `True` value.
* The standalone `baserow/backend` image when used to run a celery service now defaults
to running celery with the same number of processes as the number of available cores.
* Cache aggregation values to improve performances
* Fixed bug where the arrow keys of a selected cell didn't work when they were not
rendered.
* **Premium** Added row coloring.
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
* Added group context menu to sidebar.
* Added multi-cell pasting.
* Fixed bug where old values are missing in the update trigger of the webhook.
* Increased the max decimal places of a number field to 10.
* When the BASEROW_AMOUNT_OF_WORKERS env variable is set to blank, the amount of worker
processes defaults to the number of available cores.
* Added 0.0.0.0 and 127.0.0.1 as ALLOWED_HOSTS for connecting to the Baserow backend
* Fixed plugin boilerplate guide.
* Dropdown can now be focused with tab key
* Introduced read only lookup of foreign row by clicking on a link row relationship in
the grid view row modal.
* Select new view immediately after creation.
* Fixed bug where the link row field `link_row_relation_id` could fail when two
simultaneous requests are made.
* Fixed a bug that truncated characters for email in the sidebar
* Added `is days ago` filter to date field.
* Fix aggregation not updated on filter update
* Fixed webhook test call failing when request body is empty.
* Added Spanish and Italian languages.
* Fixed invalid `first_name` validation in the account form modal.
* Fixed a problem where a form view with link row fields sends duplicate lookup requests.
* Fixed row coloring bug when the table doesn't have any single select field.
* Upgraded node runtime to v16.14.0
* Fixed bug where a cell value was not reverted when the request to the backend fails.
* Made it possible to impersonate another user as premium admin.
* Added support in dev.sh for KDE's Konsole terminal emulator.
* Fixed a bug that would sometimes cancel multi-cell selection.
* Added batch create/update/delete rows endpoints. These endpoints make it possible to
modify multiple rows at once. Currently, row created, row updated, and row deleted
webhooks are not triggered when using these endpoints.
* Fixed Airtable import bug where the import would fail if a row is empty.
* Fixed a bug where the backend would fail hard updating token permissions for deleted tables.


## Released (2022-10-05_1.10.0)

### New features
* Added undo/redo.
* Fix formula autocomplete for fields with multiple quotes
* **breaking change** The API endpoint `/api/database/formula/<field_id>/type/` now requires
`table_id` instead of `field_id`, and also `name` in the request body.
* Added a new BASEROW_EXTRA_ALLOWED_HOSTS optional comma separated environment variable
for configuring ALLOWED_HOSTS.
* Added new endpoint to get all configured aggregations for a grid view
* Pin backend python dependencies using pip-tools.
* Added new environment variable BASEROW_FILE_UPLOAD_SIZE_LIMIT_MB
* Fixed DONT_UPDATE_FORMULAS_AFTER_MIGRATION env var not working correctly.
* Fixed the unchecked percent aggregation calculation
* Add loading bar when syncing templates to make it obvious Baserow is still loading.
* Improved backup_baserow splitting multiselect through tables in separate batches.
* Fixed a bug where making a multiple cell selection starting from an
empty `link_row` or `formula` field was not possible in Firefox.
* Allow the setting of max request page size via environment variable.
* Raise Airtable import task error and fixed a couple of minor import bugs.
* Prevent the Airtable import from failing hard when an invalid date is provided.
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
* Scroll to the first error message if the form submission fail
* Fixed bug preventing file uploads via an url for self-hosters
* Fixed translations in emails sent by Baserow.
* Added select option suggestions when converting to a select field.
* Added password protection for publicly shared grids and forms.
* Made views trashable.
* Fixed occasional UnpicklingError error when getting a value from the model cache.
* Fixed a bug for some number filters that causes all rows to be returned when text is entered.
* Fix slowdown in large Baserow instances as the generated model cache got large.
* Fixed a bug that made it possible to delete created on/modified by fields on the web frontend.
* Shared public forms now don't allow creating new options
for single and multiple select fields.
* Stopped the generated model cache clear operation also deleting all other redis keys.
* Fixed the reactivity of the row values of newly created fields in some cases.
* Boolean field converts the word `checked` to `True` value.
* The standalone `baserow/backend` image when used to run a celery service now defaults
to running celery with the same number of processes as the number of available cores.
* Cache aggregation values to improve performances
* Fixed bug where the arrow keys of a selected cell didn't work when they were not
rendered.
* **Premium** Added row coloring.
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
* Added group context menu to sidebar.
* Added multi-cell pasting.
* Fixed bug where old values are missing in the update trigger of the webhook.
* Increased the max decimal places of a number field to 10.
* When the BASEROW_AMOUNT_OF_WORKERS env variable is set to blank, the amount of worker
processes defaults to the number of available cores.
* Added 0.0.0.0 and 127.0.0.1 as ALLOWED_HOSTS for connecting to the Baserow backend
* Fixed plugin boilerplate guide.
* Dropdown can now be focused with tab key
* Introduced read only lookup of foreign row by clicking on a link row relationship in
the grid view row modal.
* Select new view immediately after creation.
* Fixed bug where the link row field `link_row_relation_id` could fail when two
simultaneous requests are made.
* Fixed a bug that truncated characters for email in the sidebar
* Added `is days ago` filter to date field.
* Fix aggregation not updated on filter update
* Fixed webhook test call failing when request body is empty.
* Added Spanish and Italian languages.
* Fixed invalid `first_name` validation in the account form modal.
* Fixed a problem where a form view with link row fields sends duplicate lookup requests.
* Fixed row coloring bug when the table doesn't have any single select field.
* Upgraded node runtime to v16.14.0
* Fixed bug where a cell value was not reverted when the request to the backend fails.
* Made it possible to impersonate another user as premium admin.
* Added support in dev.sh for KDE's Konsole terminal emulator.
* Fixed a bug that would sometimes cancel multi-cell selection.
* Added batch create/update/delete rows endpoints. These endpoints make it possible to
modify multiple rows at once. Currently, row created, row updated, and row deleted
webhooks are not triggered when using these endpoints.
* Fixed Airtable import bug where the import would fail if a row is empty.
* Fixed a bug where the backend would fail hard updating token permissions for deleted tables.


## Released (2022-03-03_1.9.1)

### New features
* Fixed API docs enum warnings. Removed `number_type` is no longer displayed in the API docs.
* Fix the Baserow Heroku install filling up the hobby postgres by disabling template
syncing by default.
* Updated templates:
  * Holiday Shopping
  * Company Asset Tracker
  * Personal Health Log
  * Recipe Book
  * Student Planner
  * Political Campaign Contributions
* Fixed bug when importing a formula or lookup field with an incorrect empty value.
* New templates:
  * Non-profit Organization Management
  * Elementary School Management
  * Call Center Log
  * Individual Medical Record
  * Trip History
  * Favorite Food Places
  * Wedding Client Planner
* Upgraded `drf-spectacular`. Flag-style query parameters like `count` will now be displayed
as `boolean` instead of `any` in the OpenAPI documentation. However, the behavior of these
flags is still the same.


## Released (2022-03-02_1.9)

### New features
* Hide "Export view" button if there is no valid exporter available
* Add Kanban view filters.
* Fixed `'<' not supported between instances of 'NoneType' and 'int'` error. Blank
string for a decimal value is now converted to `None` when using the REST API.
* Added management to import a shared Airtable base.
* Fixed error when the select row modal is closed immediately after opening.
* Add footer aggregations to grid view
* Fix restoring table linking to trashed tables creating invalid link field.
* Allow for group registrations while public registration is closed
* Fix Django's default index naming scheme causing index name collisions.
* Allow for signup via group invitation while public registration is closed.
* Workaround bug in Django's schema editor sometimes causing incorrect transaction
rollbacks resulting in the connection to the database becoming unusable.
* Add "insert left" and "insert right" field buttons to grid view head context buttons.
* Rework Baserow docker images so they can be built and tested by gitlab CI.
* Add health checks for all services.
* Added search to gallery views.
* Fix missing translation when importing empty CSV
* Migrate the Baserow Cloudron and Heroku images to work from the all-in-one.
* Cache model fields when generating model.
* Added accept `image/*` attribute to the form cover and logo upload.
* Fixed not being able to create or convert a single select field with edge case name.
* Fixed OpenAPI spec. The specification is now valid and can be used for imports to other
tools, e.g. to various REST clients.
* Added web-frontend interface to import a shared Airtable base.
* Add the all-in-one Baserow docker image.
* **breaking change** docker-compose.yml now requires secrets to be setup by the user,
listens by default on 0.0.0.0:80 with a Caddy reverse proxy, use BASEROW_PUBLIC_URL
and BASEROW_CADDY_ADDRESSES now to configure a domain with optional auto https.
* Ensure error logging is enabled in the Backend even when DEBUG is off.
* Added multi-cell selection and copying.
* Fixed adding new fields in the edit row popup that require refresh in Kanban and Form views.
* **breaking change** Number field has been changed and doesn't use `number_type` property
anymore. The property `number_decimal_places` can be now set to `0` to indicate integers
instead.
* Removed upload file size limit.
* Remove runtime mjml service and pre-render email templates at build time.
* Bumped some backend and web-frontend dependencies.
* Moved the in component `<i18n>` translations to JSON files.
* Views supporting search are properly updated when a column with a matching default value is added.


## Released (2022-01-13_1.8.2)

### New features
* Fix vuelidate issues when baserow/web-frontend used as dependency.
* Fix Table Export showing blank modal.


## Released (2022-01-13_1.8.1)

### New features
* Fixed migration failing when upgrading a version of Baserow installed using Postgres
10 or lower.
* Fixed download/preview files from another origin


## Released (2022-01-13)

### New features
* Replaced the table `order` index with an `order, id` index to improve performance.
* Allow changing the text of the submit button in the form view.
* **dev.sh users** Fixed bug in dev.sh where UID/GID were not being set correctly,
please rebuild any dev images you are using.
* Updated templates:
  * Healthcare Facility Management
  * Apartment Hunt
  * Recipe Book
  * Commercial Property Management
* Added gallery view.
  * Added cover field to the gallery view.
* Fixed frontend errors occurring sometimes when mass deleting and restoring sorted
fields
* **breaking change** The API endpoint to rotate a form views slug has been moved to
`/database/views/${viewId}/rotate-slug/`.
* Fixed bug where not all rows were displayed on large screens.
* Focused the search field when opening the modal to link a table row.
* Added day of month filter to date field.
* Improved performance by not rendering cells that are out of the view port.
* Added cover field to the Kanban view.
* New templates:
  * Car Maintenance Log
  * Teacher Lesson Plans
  * Business Conference Event
  * Restaurant Management
* Fixed copying/pasting for date field.
* Fix subtracting date intervals from dates in formulas in some situations not working.
* Increased maximum length of application name to 160 characters.
* Fixed reordering of single select options when initially creating the field.
* Added Video, Audio, PDF and some Office file preview.
* Fix the ability to make filters and sorts on invalid formula and lookup fields.
* Fix deleted options that appear in the command line JSON file export.
* Added French translation.
* Added rating field type.
* Added ability to share grid views publicly.
* Fix bug where field options in rare situations could have been duplicated.
* Fixed bug preventing trash cleanup job from running after a lookup field was converted
to another field type.
* Added length is lower than filter.
* Fixed order of fields in form preview.


## Released (2021-11-25)

### New features
* Increase Webhook URL max length to 2000.
* Fix trashing tables and related link fields causing the field dependency graph to
become invalid.
* Fixed not executing premium tests.


## Released (2021-11-24)

### New features
* Fixed a bug where the frontend would fail hard if a table with no views was accessed.
* Add aggregate formula functions and the lookup formula function.
* Made it possible to change user information.
* **Breaking Change**: Baserow's `docker-compose.yml` now allows setting the MEDIA_URL
env variable. If using MEDIA_PORT you now need to set MEDIA_URL also.
* Added the kanban view.
* Added extra indexes for user tables increasing performance.
* Updated templates:
  * Commercial Property Management
  * Company Asset Tracker
  * Wedding Planner
  * Blog Post Management
  * Home Inventory
  * Book Writing Guide
  * Political Campaign Contributions
  * Applicant Tracker
* Fixed propType validation error when converting from a date field to a boolean field.
* Tables can now be opened in new browser tabs.
* Added table webhooks functionality.
* Fixed a bug where the frontend would fail hard when converting a multiple select field
inside the row edit modal.
* Fixed bug where it was possible to create duplicate trash entries.
* New templates:
  * House Search
  * Personal Health Log
  * Job Search
  * Single Trip Planner
  * Software Application Bug Tracker
* Deprecate internal formula field function field_by_id.
* Added a licensing system for the premium version.
* **Breaking Change**: Baserow's `docker-compose.yml` container names have changed to
no longer be hardcoded to prevent naming clashes.
* Fixed date_diff formula function.
* Add lookup field type.


## Released (2021-10-05)

### New features
* Introduced new endpoint to get and update user account information.
* Fixed bug where sometimes fields would not be ordered correctly in view exports.
* Fixed bug where a user could not be edited in the admin interface without providing
a password.
* Fixed bug where the backend would fail hard when an invalid integer was provided as
'before_id' when moving a row by introducing a decorator to validate query parameters.
* Updated templates:
  * Blog Post Management
* Fixed error when rapidly switching between template tables or views in the template
preview.
* Fixed a bug where the currently selected view was not in the viewport of the parent.
* Fixed bug where brand-new fields weren't included in view exports.
* Added "Multiple Select" field type.
* Upgraded Django to version 3.2.6 and also upgraded all other backend libraries to
their latest versions.
* Fix minor error that could sometimes occur when a row and it's table/group/database
were deleted in rapid succession.
* Importing table data with a column name that is too long will now truncate that name.
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
* Fixed error when pasting into a single select field.
* Fixed a bug where the backend would fail hard when trying to order by field name without
using `user_field_names`.
* Fixed bug where copying a cell containing a null value resulted in an error.
* Fix accidentally locking of too many rows in various tables during update operations.
* The API now returns appropriate errors when trying to create a field with a name which is too long.
* Fixed a bug where views context would not scroll down after a new view has been added.
* Added "Formula" field type with 30+ useful functions allowing dynamic per row
calculations.
* Pasting the value of a single select option into a single select field now selects the
first option with that value.
* Introduced the has file type filter.


## Released (2021-08-11)

### New features
* Made the form view compatible with importing and exporting.
* Made it possible to use the "F2"-Key to edit a cell without clearing the cell content.
* Bumped the dependencies.
* Enabled password validation in the backend.
* Added steps on how to configure Baserow to send emails in the install-on-ubuntu guide.
* Updated templates:
  * Personal Task Manager
  * Wedding Planning
  * Book Catalog
  * Applicant Tracker
  * Project Tracker
* The internal setting allowing Baserow to run with the user tables in a separate
database has been removed entirely to prevent data integrity issues.
* Fixed moment issue if core is installed as a dependency.
* Add backup and restore database management commands.
* Fixed bug where the currently selected dropdown item is out of view from the dropdown
window when scrolling with the arrow keys.
* **Premium**: You can now comment and discuss rows with others in your group, click the
expand row button at the start of the row to view and add comments.
* Relaxed the URL field validator and made it consistent between the backend and
web-frontend.
* New templates:
  * Blog Post Management
* Made it possible to leave a group.
* Dropped the `old_name` column.
* Changed web-frontend `/api/docs` route into `/api-docs`.
* Added password validation to password reset page.
* Introduced link row field has row filter.
* Added "Last Modified" and "Created On" field types.
* Fixed nuxt not restarting correctly using the provided Baserow supervisor config file.
* Fixed earliest and latest date aggregations
* Hide view types that can't be exported in the export modal.


## Released (2021-07-16)

### New features
* Fix bug preventing fields not being able to be converted to link row fields in some
situations.


## Released (2021-07-15)

### New features
* **Breaking Change**: `docker-compose.yml` will by default only expose Baserow on
`localhost` and not `0.0.0.0`, meaning it will not be accessible remotely unless
manually configured.
* **Breaking Change**: Baserow's `docker-compose.yml` no longer exposes ports for
the `db`, `mjml` and `redis` containers for security reasons.


## Released (2021-07-13)

### New features
* Fixed error in trash cleanup job when deleting multiple rows and a field from the
same table at once.
* Fixed bug preventing the deletion of rows with a blank single select primary field.
* Added a Heroku template and one click deploy button.


## Released (2021-07-12)

### New features
* Single select options can now be ordered by drag and drop.
* Fix the create group invite endpoint failing when no message provided.
* Support building Baserow out of the box on Ubuntu by lowering the required docker
version to build Baserow down to 19.03.
* Add trash where deleted apps, groups, tables, fields and rows can be restored
deletion.
* Made it possible to list table field meta-data with a token.
* The email field's validation is now consistent and much more permissive allowing most
values which look like email addresses.
* Add user_field_names GET flag to various endpoints which switches the API to work
using actual field names and not the internal field_1,field_2 etc identifiers.
* The API endpoint to update the grid view field options has been moved to
`/api/database/views/{view_id}/field-options/`.
* Disallow duplicate field names in the same table, blank field names or field names
called 'order' and 'id'. Existing invalid field names will be fixed automatically.
* Added templates:
  * Commercial Property Management
  * Company Asset Tracker
  * Student Planner
* Added before and after date filters.
* Added form view.


## Released (2021-06-02)

### New features
* Made it possible to order the tables by drag and drop.
* Made it possible to order the applications by drag and drop.
* **Premium**: Added an admin dashboard.
* **Premium**: Added group admin area allowing management of all baserow groups.
* Added a page containing external resources to the docs.
* Made it possible to order the groups by drag and drop.
* Fixed bug where the focus of an Editable component was not always during and after
editing if the parent component had overflow hidden.
* Templates:
  * Lightweight CRM
  * Wedding Planning
  * Book Catalog
  * App Pitch Planner
* Tables and views can now be exported to CSV (if you have installed using the ubuntu
guide please use the updated .conf files to enable this feature).
* Added a human-readable error message when a user tries to sign in with a deactivated
account.
* Removed URL field max length and fixed the backend failing hard because of that.
* Fixed bug where the grid view would fail hard if a cell is selected and the component
is destroyed.
* Made it possible to import a JSON file when creating a table.
* Made it possible to order the views by drag and drop.
* **Premium** Tables and views can now be exported to JSON and XML.
* Added today, this month and this year filter.
* Fixed bug where the selected view would still be visible after deleting it.


## Released (2021-05-11)

### New features
* **Premium**: Added user admin area allowing management of all baserow users.
* Switch to using a celery based email backend by default.
* Fixed bug where the rows could get out of sync during real time collaboration.
* Make the view header more compact when the content doesn't fit anymore.
* Added `--add-columns` flag to the `fill_table` management command. It creates all the
field types before filling the table with random data.
* Made it possible to drag and drop the views in the desired order.
* Reworked Baserow's Docker setup to be easier to use, faster to build and more secure.
* Made it possible to drag and drop rows in the desired order.
* Allow providing a `template_id` when registering a new account, which will install
that template instead of the default database.
* Fixed memory leak in the `link_row` field.
* Added `fill_users` admin management command which fills baserow with fake users.
* Added configurable field limit.
* Made it possible to export and import the file field including contents.


## Released (2021-04-08)

### New features
* The list_database_table_rows search query parameter now searches all possible field
types.
* Added support for different** character encodings when importing CSV files.
* Fixed SSRF bug in the file upload by URL by blocking urls to the private network.
* Made it possible to re-order fields in a grid view.
* Remove incorrectly included "filters_disabled" field from
list_database_table_grid_view_rows api endpoint.
* Fixed bug where an invalid date could be converted to 0001-01-01.
* Fixed 100X backend web socket errors when refreshing the page.
* Show an error to the user when the web socket connection could not be made and the
reconnect loop stops.
* Add Phone Number field.
* Add missing include query parameter and corresponding response attributes to API docs.
* The first user to sign-up after installation now gets given staff status.
* Show the number of filters and sorts active in the header of a grid view.
* Add support for Date, Number and Single Select fields to the Contains and Not Contains
view
filters.
* Searching all rows can now be done by clicking the new search icon in the top right.
* Prevent websocket reconnect when the connection closes without error.
* Refactored the GridView component and improved interface speed.
* Added support for importing tables from XML files.
* Prevent websocket reconnect loop when the authentication fails.
* Rename the "includes" get parameter across all API endpoints to "include" to be
consistent.
* Added gunicorn worker test to the CI pipeline.


## Released (2021-03-01)

### New features
* Made it possible for the admin to disable new signups.
* Added a field type filename contains filter.
* Refactored the has_user everywhere such that the raise_error argument is used when
possible.
* Use UTC time in the date picker.
* Redesigned the left sidebar.
* Reduced the amount of queries when using the link row field.
* Added single select field form option validation.
* Fail hard when the web-frontend can't reach the backend because of a network error.
* Added field name to the public REST API docs.
* Fixed bug where the Editable component was not working if a prent a user-select:
none; property.
* Changed all cookies to SameSite=lax.
* Fixed bug where a single select field without options could not be converted to a
another field.
* Made the public REST API docs compatible with smaller screens.
* Upgraded DRF Spectacular dependency to the latest version.
* Respect the date format when converting to a date field.
* Fixed the "Ignored attempt to cancel a touchmove" error.
* Refactored handler get_* methods so that they never check for permissions.
* Made it possible to configure SMTP settings via environment variables.
* Added Baserow Cloudron app.
* Fixed error when a very long user file name is provided when uploading.


## Released (2021-02-04)

### New features
* Upgraded web-frontend dependencies.
* Keep token usage details.
* Fixed bug where is was not possible to create a relation to a table that has a single
select as primary field.
* Fixed bug where you could not convert an existing field to a single select field
without select options.
* Made it possible to invite other users to a group.
* Added option to hide fields in a grid view.
* Fixed bug where the row in the RowEditModel was not entirely reactive and wouldn't be
updated when the grid view was refreshed.
* Implemented real time collaboration.
* Fixed bug where an incompatible row value was visible and used while changing the
field type.


## Released (2021-01-06)

### New features
* Added filtering by GET parameter to the rows listing endpoint.
* Fixed bug where if you have no filters, but the filter type is set to `OR` it always
results in a not matching row state in the web-frontend.
* Made the file name editable.
* Made it possible to include or exclude specific fields when listing rows via the API.
* Allow larger values for the number field and improved the validation.
* Fixed drifting context menu.
* Fixed bug where the page refreshes if you press enter in an input in the row modal.
* Fixed bug where the arrow navigation didn't work for the dropdown component in
combination with a search query.
* Store updated and created timestamp for the groups, applications, tables, views,
fields and rows.
* Implemented a single select field.
* Made the rows orderable and added the ability to insert a row at a given position.
* Fixed bug where inserting above or below a row created upon signup doesn't work
correctly.


## Released (2020-12-01)

### New features
* Also lint the backend tests.
* Implemented a switch to disable all filters without deleting them.
* Set un-secure lax cookie when public web frontend url isn't over a secure connection.
* Fixed API docs scrollbar size issue.
* Made the cookies strict and secure.
* Added community chat to the readme.
* Made it possible to order by fields via the rows listing endpoint.
* Added select_for_update where it was still missing.
* Made it impossible for the `link_row` field to be a primary field because that can
cause the primary field to be deleted.
* Implemented a file field and user files upload.
* Removed the redundant _DOMAIN variables.
* Fixed bug where the sort choose field item didn't have a hover effect.


## Released (2020-11-02)

### New features
* Highlight the row of a selected cell.
* Added confirmation modals when the user wants to delete a group, application, table,
view or field.
* Added importer abstraction including a CSV and tabular paste importer.
* Added Ubuntu installation guide documentation.
* Fixed error when there is no view.
* Made it possible to publicly expose the table data via a REST API.
* Added Email field.
* Fixed bug in the web-frontend URL validation where a '*' was invalidates.
* Added ability to navigate dropdown menus with arrow keys.


## Released (2020-10-06)

### New features
* Fixed The table X is not found in the store error.
* Fixed bug where the link row field is not removed from the store when the related
table is deleted.
* Added filtering of rows per view.
* Added URL field.
* Added sorting of rows per view.
* Prevent adding a new line to the long text field in the grid view when selecting the
cell by pressing the enter key.
* Fixed bug where the error message of the 'Select a table to link to' was not always
displayed.
* Fixed bug where the selected name of the dropdown was not updated when that name was
changed.


## Released (2020-09-02)

### New features
* Added contribution guidelines.
* Fixed bug where it was not possible to change the table name when it contained a link
row field.


## Released (2020-08-31)

### New features
* Increased the amount of password characters to 256 when signing up.
* Added field that can link to the row of another table.
* Fixed bug where the text_default value changed to None if not provided in a patch
request.
* Block non web frontend domains in the base url when requesting a password reset
email.
* Show machine readable error message when the signature has expired.


## Released (2020-07-20)

### New features
* Added OpenAPI docs.
* Removed not needed api v0 namespace in url and python module.
* Use the new long text field, date field and view's field options for the example
tables when creating a new account. Also use the long text field when creating a new
table.
* Added raises attribute to the docstrings.
* Added cookiecutter plugin boilerplate.
* Refactored all SCSS classes to BEM naming.
* Improved API 404 errors by providing a machine readable error.
* Fixed keeping the datepicker visible in the grid view when selecting a date for the
first time.
* Added documentation markdown files.


## Released (2020-06-08)

### New features
* Implemented reset forgotten password functionality.
* Prevent row context menu when right clicking on a field that's being edited.
* Normalize the users email address when signing up and signing in.
* Added date/datetime field.
* Made it possible to resize the field width per view.
* Use environment variables for all settings.
* Added row modal editing feature to the grid view.
* Changed the styling of the notification alerts.
* Fixed memory leak bug.
* Fill a newly created table with some initial data.
* Fixed error when changing field type and the data value wasn't in the correct
format.
* Added validation and formatting for the number field.
* Fixed not refreshing token bug and improved authentication a little bit.
* Use Django REST framework status code constants instead of integers.
* Cancel the editing state of a fields when the escape key is pressed.
* Introduced copy, paste and delete functionality of selected fields.
* The next field is now selected when the tab character is pressed when a field is
selected.
* Enabled the arrow keys to navigate through the fields in the grid view.
* Improved grid view scrolling for touch devices.
* Added long text field.
* Update the field's data values when the type changes.
* Implemented password change function and settings popup.
* Fixed not handling 500 errors.


