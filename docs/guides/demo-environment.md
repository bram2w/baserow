# Demo environment

If you just want to try out Baserow on your local computer, it is best to start the 
demo environment via `docker-compose`.

## Installing requirements

If you haven't already installed docker and docker-compose on your computer you can do
so by following the instructions on https://docs.docker.com/desktop/.

If you haven't already installed git you can do so by following the instructions on 
https://www.linode.com/docs/development/version-control/how-to-install-git-on-linux-mac-and-windows/.

Once you have finished installing all the required software you should able to run the
following commands in your terminal.

```
$ docker -v
Docker version 19.03.8, build afacb8b
$ docker-compose -v
docker-compose version 1.25.5, build 8a1c60f6
$ git --version
git version 2.24.3 (Apple Git-128)
```

If all commands return something similar as described in the example, then you are 
ready to proceed!

## Starting demo environment

> Note that this has only been tested on MacOS Catalina. If you run into any issues 
> with other operating systems, feel free to contact us via the form on
> https://baserow.io/contact.

For example purposes I have created a directory in my home folder named `baserow-demo`.
You can of course follow the steps in any directory, but in this tutorial I will assume
the working directory is `~/baserow-demo`.

First we have to clone the repository. Execute the following commands to clone the 
master branch. If you are not familiar with git clone, this will download a copy 
Baserow's code to your computer.

```
$ cd ~/baserow-demo
$ git clone git@gitlab.com:bramw/baserow.git
Cloning into 'baserow'...
...
$ cd baserow
```

Now that we have our copy and we moved inside the newly created `baserow` directory, we 
can get started. You just have to execute the docker-compose command using the 
`docker-compose.demo.yml` file. It might take a while for the command finishes, this is 
because the image has to be created from scratch.

```
$ docker network create baserow_demo_default
$ docker-compose -f docker-compose.demo.yml up
Building backend
...
Starting baserow_db_1   ... done
Starting baserow_mjml_1 ... done
Starting backend        ... done
Starting web-frontend   ... done
```

Once everything has finished and you can visit http://localhost:3000 in your browser
and you should be redirected to the login screen. Via here you can create a new account
and start using the software.

> I strongly discourage running these images in production. These are just for demo
> purposes only.
