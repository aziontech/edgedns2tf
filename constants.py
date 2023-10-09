TERRAFORM_INITAL_CONTENT='''terraform {
  required_providers {
    azion = {
      source = "aziontech/azion"
      version = "~> 1.16.0"
    }
  }
}

'''

TERRAFORM_IDNS_DATA='''
data "azion_intelligent_dns_zones" "all_zones" {
  page_size = 1000000
}

data "azion_intelligent_dns_records" "records" {
  for_each = { for zone in data.azion_intelligent_dns_zones.all_zones.results : zone.zone_id => zone }
  zone_id = each.value.zone_id
  page_size = 1000000
}

'''

OUTPUT_PATH = 'output'
TF_STATE = 'terraform.tfstate'
