# Setting up a Docker Hub pull-through cache

## Context

In light of the pull-rate limits, we are investigating what we can do at Sage to minimize the number of requests we send out to Docker Hub. One option explored here is the setup of a local pull-through cache on individual EC2 instances. Admittedly, individual instances won't run into pull-rate limits most of the time. That said, we still would like to minimize needless internet traffic, especially since most of our Docker Hub usage involves tagged images (for reproducibility) that shouldn't change over time. The experience from this small-scale experiment could also inform what solution we will deploy to address the issue for batch computing (_e.g._ AWS Batch, Toil cluster), where rate limits are more of an immediate problem.

## Setup

### Quick start

This setup was put together based on [pull-through cache documentation](https://docs.docker.com/registry/recipes/mirror/). The following Bash commands were run on an `EC2: Ubuntu Linux with Workflow Software` instance provisioned through the Service Catalog. Note that I manually installed `docker-compose` using [these instructions](https://docs.docker.com/compose/install/#install-compose-on-linux-systems).

```bash
# Install docker-compose on 'Ubuntu Linux with Workflow Software' instance
sudo curl -L "https://github.com/docker/compose/releases/download/1.27.4/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Update Docker to use the recently added '--pull' option in 'docker run'
sudo apt-get update
sudo apt-get install docker-ce-cli

# Set up local Docker registry as pull-through cache using custom config.yml
# Parameters for `docker run` tracked in docker-compose.yml for brevity
docker-compose --file docker-compose.yml up --detach

# Confirm that the pull-through cache is set up properly
# The '--pull always' is there to ignore cached versions
docker run --pull always localhost:5000/library/alpine

# Configure Docker daemon to use the new pull-through cache
sudo cp ./daemon.json /etc/docker/daemon.json
sudo systemctl restart docker

# Confirm that the Docker daemon is set up properly
# Note that the 'localhost:5000/' prefix is omitted
docker run --pull always alpine
```

### Before/after local pull-through cache

You can compare the output from trying to use `docker run` before and after instantiating the local pull-through cache. I'm using `--pull always` to ignore cached versions, but I've also pruned the local images first with `docker system prune -a`.

```
$ docker run --pull always localhost:5000/library/alpine
docker: Error response from daemon: Get http://localhost:5000/v2/: dial tcp 127.0.0.1:5000: connect: connection refused.
See 'docker run --help'.

$ docker-compose --file docker-compose.yml up --detach
Creating localcache ... done

$ docker run --pull always localhost:5000/library/alpine
latest: Pulling from library/alpine
Digest: sha256:3c7497bf0c7af93428242d6176e8f7905f2201d8fc5861f45be7a346b5f23436
Status: Image is up to date for localhost:5000/library/alpine:latest
```

### Before/after Docker daemon configuration

You can compare the output from scanning `scheduler-state.json` for `alpine` before and after configuring the Docker daemon to use the local pull-through cache. Note that we don't need to prefix the image with `localhost:5000/` and we don't need to use the `library/` namespace.

```
$ docker exec localcache grep -c alpine /var/lib/registry/scheduler-state.json
0

$ docker run --pull always alpine
[...]
Status: Downloaded newer image for alpine:latest

$ docker exec localcache grep -c alpine /var/lib/registry/scheduler-state.json
1
```

## Additional Notes

- During my research, I came across [`docker-registry-proxy`](https://hub.docker.com/r/tiangolo/docker-registry-proxy). From what I can tell, this Docker image tries to solve a similar issue, except it adds support for registries other than Docker Hub, which isn't supported in the pull-through cache. This will be important if we want to deploy our images to multiple registries such as Quay.io.

- We should be mindful of the following warning if we use Docker Hub credentials. I'm not too concerned if we configure these caches to be only accessible from within the network. In my example above, I explicitly bind the port to `localhost`.

  > **Warning:** If you specify a username and password, it’s very important to understand that private resources that this user has access to Docker Hub is made available on your mirror. You must secure your mirror by implementing authentication if you expect these resources to stay private!

- I confirmed that the `filesystem` driver is used for storage in the registry configuration file. I decided to turn off the in-memory cache `storage` option because the pull-through cache isn't running on its own server and I figured that memory probably best be used by the computational jobs running on the instance.

- I also enabled the `delete` option in the registry configuration to allow for the periodic clean-up of older content. This was a recommendation in the [documentation](https://docs.docker.com/registry/recipes/mirror/).
