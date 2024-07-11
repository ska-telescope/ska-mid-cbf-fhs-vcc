
# Boogie Container
This docker image contains an installed version of boogie which you can run and interact with tango by setting its TANGO_HOST to connect to the relevant Tango DB inside the container.


## Building
From the root project folder run

```
docker build -t boogie_runner -f ./images/boogie/Dockerfile .
```

## Running
Running exposes the host port 10000 and container port 10000

Note:  while it isn't super secure using -net=host as it shares the host network isntead of creating its own, its simple and works for this case

```
docker run -it --name boogie_runner -net=host boogie_runner
```