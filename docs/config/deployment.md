# Deployment options in configuration file

Deployment options are usually provided in the [main configuration file](../configurations.md) and wrapped around the `ecflow_server` section which are directly related to the server configuration.

> **Important**: The ecflow server configuration is not to be confused with the **execution host** which is described in the [host](./host.md) section. In systems with shared filesystems, like ECMWF's ATOS HPC, the execution host looks like the same as the deployment host, but this is not always the case. They can be different and the ecflow server will be responsible for the communication (sending job files, fetching outputs, etc) with the execution host. The deployment host is where the suite definition file and scripts will be deployed, therefore should be a location accessible by the ecflow server, while the execution host is where the tasks will be executed.


To deploy the suite, the following options are required:
```yaml
suite_name: experiment1
ecflow_server:
    user: username
    hostname: hostname
    deploy_dir: /path/to/deploy/dir
```

For a full set of deployment options please refer to the [deployment section](../tracksuite_guide.md).
