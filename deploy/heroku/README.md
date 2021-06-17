## Testing

In order to test your changes you need to have to Heroku command line installed on your
local machine. Next, you can use the Heroku command line to create an app, manually
install the `addons` and `labs` listed in the app.json file at the root of this repo.
In the example below we assume we are at the roow of the Baserow repo and we are going
install a heroku app named `baserow-test-app`, this can of course be named differently.

```
$ heroku apps:create baserow-test-app
$ heroku stack:set -a baserow-test-app container

# We need to add all the addons listed in the app.json file
$ heroku addons:create -a baserow-test-app heroku-postgresql:hobby-dev
$ heroku addons:create -a baserow-test-app stackhero-redis:test
$ heroku addons:create -a baserow-test-app mailgun:starter

# The `stackhero-redis:test` can optionally be replaced by `heroku-redis:hobby-dev`,
# but their free plan doesn't support enough simultanious connections. So it is
# recommended to at least get the `heroku-redis:premium-0`. Note that the 
# `stackhero-redis:test` must be removed first because that URL has priority.
# $ heroku addons:destroy -a baserow-test-app stackhero-redis:test
# $ heroku addons:create -a baserow-test-app heroku-redis:premium-0

# We need to add all the labs listed in the app.json file.
$ heroku labs:enable -a baserow-test-app runtime-dyno-metadata

# Finally we need to set all the environment variables listed in the app.json file.
$ heroku config:set -a baserow-test-app SECRET_KEY=REPLACE_WITH_SECRET_VALUE
$ heroku config:set -a baserow-test-app BASEROW_PUBLIC_URL=
$ heroku config:set -a baserow-test-app BASEROW_AMOUNT_OF_WORKERS=1
```

Now that we have replicated the setup of the app.json, we can deploy the application
by pushing to the heroku remote repository.

> Make sure that you have commited all the changes before pushing.

```
$ git push heroku YOUR_CURRENT_BRANCH:master
```
