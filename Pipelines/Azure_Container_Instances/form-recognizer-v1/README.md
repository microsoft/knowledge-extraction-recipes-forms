# Deploying Form Recognizer V1 to Azure Container Instances

The deployment is done via Terraform. In order to do this you need
to provide certain values in order to execute the terraform script. 
The definition of the required variables are defined in `variables.tf`

In order to deploy the execute

```bash
terraform init

terraform apply
```

The outputs will provide the necessary URI to use the service endpoints.