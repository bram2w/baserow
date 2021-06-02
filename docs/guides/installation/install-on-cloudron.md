# Installation on Cloudron

Cloudron is a complete solution for running apps on your server and keeping them
up-to-date and secure. If you don't have Cloudron installed on a server you can follow
the [installation instructions here ](https://docs.cloudron.io/installation/). 
Ensure you follow the installation guide to the end and log into the cloudron app store.
Once you have Cloudron installed and running on your service you can follow the steps below 
to install the Baserow app.

> Basic experience with the Cloudron CLI is required.

## Install Cloudron CLI

The Cloudron CLI runs on your local machine and not the server. It can be installed on 
Linux/Mac using the following command. More information about installing can be found on 
their website at
[https://docs.cloudron.io/custom-apps/cli/](https://docs.cloudron.io/custom-apps/cli/).

```
$ # Do not attempt to install on your server, but instead on your local machine.
$ sudo npm install -g cloudron
```

## Installing Baserow

If you have not already been logged into your Cloudron platform you can do so by
executing the following command.

```
$ cloudron login my.{YOUR_DOMAIN}
```

When you have successfully logged in, you need to clone the latest Baserow repository
to your machine. This contains the Cloudron manifest file that you need when installing
the app.

```
$ git clone --branch master https://gitlab.com/bramw/baserow.git
$ cd baserow/deploy/cloudron
```

After that you can install the Baserow Cloudron app by executing the following commands.

```
$ cloudron install -l baserow.{YOUR_DOMAIN} --image registry.gitlab.com/bramw/baserow/cloudron:1.3.0
App is being installed.
...
App is installed.
```

> All the available versions can be found here:
> [https://gitlab.com/bramw/baserow/container_registry/1692077](https://gitlab.com/bramw/baserow/container_registry/1692077)

> If you get Failed to install app: 402 message: Missing token errors make sure you 
> have fully completed the installation of the cloudron server linked at the start. 
> Specifically you need to login to your cloudron account on your server's cloudron 
> webpage.

When the installation has finished you can visit your domain and create a new account
from there.

## Updating

When a new Baserow version becomes available you can easily update to that version.
First you need to figure out what your app id is. You can do so by executing the
`cloudron list` command. After that you can execute the following command to update to
the latest version.

```
cloudron update --app {YOUR_APP_ID} --image registry.gitlab.com/bramw/baserow/cloudron:1.3.0
```

> Note that you must replace the image with the most recent image of Baserow. The
> latest version can be found here: 
> [https://gitlab.com/bramw/baserow/container_registry/1692077](https://gitlab.com/bramw/baserow/container_registry/1692077)

