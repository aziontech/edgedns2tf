#!/usr/bin/python3

import os
import sys
import subprocess
import genconf
import genstate
from util import get_terraform_bin

def main():
    
    TOKEN = os.getenv("AZION_API_TOKEN")
    if TOKEN is None or TOKEN == "":
        print("Please, execute export AZION_API_TOKEN=<token>")
        sys.exit(1)

    if get_terraform_bin('terraform') is None:
        print('Terraform binary not found!')
        sys.exit(1)

    print("> Terraform State: Extrating iDNS Zones and Records...")
    generator = genstate.TerraformStateGenerator("intermediate")
    has_zones = generator.create_early_state()
    print("> Terraform State: Extration done")

    if has_zones:
        print("> Terraform State: Creating Terraform State...")
        generator.create_finally_state()
    print("> Terraform State: Done")

    print("> Terraform Config: Creating Terraform Config...")
    conf = genconf.TerraformGenConfig("terraform.tf")
    conf.generate_terraform_config()
    print("> Terraform Config: Done")

if __name__ == '__main__':
    main()