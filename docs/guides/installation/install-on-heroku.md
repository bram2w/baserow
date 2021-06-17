# Installation on Heroku

Heroku is a platform as a service that enabled developer to build, run and operate
applications entirely in the cloud. We have created a template that allows you to
easily Baserow on the free plan of Heroku. You can easily scale up by tweaking some settings


## The template

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy/?template=https://heroku.com/deploy?template=https://gitlab.com/bramw/baserow)

The button above can be used install Baserow on Heroku with one click. Click on it and
follow the steps on heroku.com to proceed. After the installation you can reach Baserow
on URL provided by Heroku.

## Persistent S3 file storage

By default, the uploaded files are stored inside the dyno for demo purposes. This means
that everytime your dyno restarts, you will lose all your uploaded files.

## Scaling

Even though the template runs on the free plan of Heroku by default, it can easily be
scaled up to fit your needs. We recommend scaling up if you are going to use Baserow
with more than one users simultaneously. You can easily scale up by changing the type
and increase the amount of dyno's.

To safe resources, by default every dyno has only one worker. If you are upgrading to
a standarad or performance dyno, you can easily increase the amount of workers to 4.
This can be done via the Config Vars in the Settings. On the settings page, click on 
"Reveal Config Vars", find the "BASEROW_AMOUNT_OF_WORKERS" var and set the value to 4.

## Redis

## Environment variables
