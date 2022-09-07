# Prefill Forms
Forms can be prefilled in order to help the user fill in the form faster.

All fields which are available in the form can be prefilled.

## How to prefill a form
If you want to prefill a form with data you can do so via query parameters
added to the public form url. These query parameters are prefixed with
`prefill` to avoid any collision with potential future query parameters.

### Format
The format of the query parameters is as follows:
````
?prefill_<field_name>=<value>
````

### Example
In the example below we want to prefill a field called `Name` with the value of `Mike`
````
?prefill_Name=Mike
````

### Spaces
Spaces in the field name are replaced with `+` to avoid any issues with the query parameter.
````
?prefill_my+field=Mike
````

### Multiple values
If you want to prefill multiple fields you can do so by adding a `,` between the values.
````
?prefill_multi+select=Mike,John
````

### Special Field Types
Generally the prefill value is the same as the value of the field. But there are some exceptions
where the value is translated to a different value.

#### Rating field
A rating field accepts a number to indicate how many stars should be filled.
````
?prefill_rating=3
````

#### Link Row Field
A link row field can accept the value that is shown in the select dropdown.
````
?prefill_link+row=Mike
````

#### Single Select / Multiple Select field
A single select field can accept the value that is shown in the select dropdown.
So does the Multiple Select field, but it can also accept multiple values.
````
?prefill_single+select=Mike
````

#### Date Field
A date field can accept a date in the following formats and will use the date format
of the field to parse the date.
````
// Standards
ISO_8601

// General formats
'YYYY-MM-DD',
'YYYY-MM-DD hh:mm A',
'YYYY-MM-DD HH:mm',

// EU
'DD/MM/YYYY', 
'DD/MM/YYYY hh:mm A', 
'DD/MM/YYYY HH:mm'

// US
'MM/DD/YYYY', 
'MM/DD/YYYY hh:mm A', 
'MM/DD/YYYY HH:mm'
````





