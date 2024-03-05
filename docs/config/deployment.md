# Deployment options in configuration file

Deployment options are usually provided in the [main configuration file](../configurations.md).
The options are used by the deployment [wellies.deploy_suite][] function, as described in the [deployment section](../tracksuite_guide.md).
To deploy the suite, the following options are required:
```yaml
suite_name: mysuite
user: username
deploy_hostname: hostname
deploy_dir: /path/to/deploy/dir
backup_deploy: git@github.com:myrepo.git  # optional
```
