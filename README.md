# idns2tf

IDNS2TF simplify the extraction of Azion Edge DNS configurations and creation of Terraform configuration files based on zones and obtained DNS records.

That tool is especially useful if you intend to manage your DNS settings in the GitOps model.

## Before Use
Make check if the dependencies are met in your environment.

* [Terraform](https://www.terraform.io/downloads.html) 1.5.x or higher.
* Check if application dependencies are installed:

```
pip3 install -r requirements.txt
```
Alternatively, you can use the Docker command container version, where all of this has been already taken care for you.

## How to use?

If running the script directly:
```
AZION_API_TOKEN=<azion_api_token> python3 idns2tf.py
```
Or, using the custom Docker command container:
```
AZION_API_TOKEN=<azion_api_token> docker-compose run --rm --build idns2tf
```

Your DNS configurations (in Terraform format) + the Terraform state will be available in the **output** folder after the execution. 

The generated files are named as follows: **zone_<zone_id>.tf**. Inside each file are the DNS Zone configurations and related Records and DNSSEC.
