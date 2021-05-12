# Running Baserow locally 

If you just want to try out Baserow on your local computer, it is best to use 
`docker-compose`. The provided `docker-compose.yml` file will launch a production 
version of Baserow and can be used to run Baserow locally or as a starting point for 
building your own production Baserow setup.


### Quickstart 
If you are familiar with git and docker-compose run these commands to launch baserow 
locally, otherwise please start from the Installing Requirements section below.
```bash
$ git clone https://gitlab.com/bramw/baserow.git
$ cd baserow
$ docker-compose up
```

## Installing requirements

If you haven't already installed docker and docker-compose on your computer you can do
so by following the instructions on https://docs.docker.com/desktop/ and 
https://docs.docker.com/compose/install/.

> Docker version 20.10.0 is the minimum required to build Baserow. Please ensure your
> your docker is up to date by running `docker -v`.

You will also need git installed which you can do by following the instructions on 
https://www.linode.com/docs/development/version-control/how-to-install-git-on-linux-mac-and-windows/.

After installing all the required software you should be able to run the
following commands in your terminal.

```
$ docker -v
Docker version 20.10.6, build 370c289
$ docker-compose -v
docker-compose version 1.26.2, build eefe0d31
$ git --version
git version 2.24.3 (Apple Git-128)
```

If all commands return something similar as described in the example, then you are 
ready to proceed!

## Starting baserow using docker-compose 

> Note that this has only been tested on MacOS Catalina and Ubuntu 20.04. If you run 
> into any issues with other operating systems, feel free to contact us via the form on
> https://baserow.io/contact.

For example purposes I have created a directory in my home folder named `baserow`.
You can of course follow the steps in any directory, but in this tutorial I will assume
the working directory is `~/baserow`.

First we have to clone the repository. Execute the following commands to clone the 
master branch. If you are not familiar with git clone, this will download a copy 
Baserow's code to your computer.

```
$ cd ~/baserow
$ git clone https://gitlab.com/bramw/baserow.git
Cloning into 'baserow'...
...
$ cd baserow
```

Now that we have our copy of the repo and have changed directories to the newly 
created `baserow`, we can bring up the containers. You just have to execute the 
`docker-compose up` command. It might take a while for the command to finish, this is 
because the image has to be built from scratch.

```
$ docker-compose up
Building backend
...
Starting db             ... done
Starting mjml           ... done
Starting backend        ... done
Starting celery         ... done
Starting web-frontend   ... done
```

Once everything has finished, you can visit http://localhost:3000 in your browser
and you should be redirected to the login screen. From here you can create a new account
and start using the software.

## Further Reading
- See [docker how to guide](baserow-docker-how-to.md) for a larger collection of
  useful operations and commands.
- See [docker usage](../reference/baserow-docker-api.md) for more detail on how
  Baserow's docker setup can be used and configured.
