Baserow is an open source no-code database tool and Airtable alternative. Easily create
a relational database without any technical expertise. Build a table and define custom
fields like text, number, file and many more.

## Application builder domains

Baserow has an application builder that allows to deploy an application to a specific
domain. Because Cloudron has a reverse proxy that routes a domain to the right Cloudron
app, the deployed application isn't automatically available on the chosen domain.

To make this work, you must add a domain alias in the Cloudron settings. This can be
done by going to the settings of your Baserow app, then click on `Location`, click on
`Add an alias`, and then add the domain you've published the application to in Baserow.
Make sure that the alias matches the full domain name in Baserow. After that, Cloudron
will request the SSL certificate, and then you can visit your domain.

It's also possible to add a wildcard alias to Cloudron, but the SSL certificate then
doesn't work out of the box. Some additional settings on Cloudron might be required to
make it work.
