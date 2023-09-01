import subprocess
import re
import os
import constants
import util

class TerraformStateGenerator:
    def __init__(self, file_name):
        self.file_name = file_name
        self.zone_code = ""
        self.records_code = ""
        self.import_idns = []

    def _terraform_mk_conf(self):
        try:
            with open(f"./{self.file_name}_tmp.tf", "w", encoding="utf-8") as file:
                file.write(constants.TERRAFORM_INITAL_CONTENT)
                file.write(constants.TERRAFORM_IDNS_DATA)
        except OSError as e:
            print(f'Could not open/read file: {self.file_name}')

    def _init_context(self):
        subprocess.run(["terraform", "init"], encoding="utf-8", stdout=subprocess.DEVNULL, check=False)
        subprocess.run(["terraform", "apply"], encoding="utf-8", stdout=subprocess.DEVNULL, check=False)

    def _parse_state_output(self):
        #Get the TF state data
        state_output = subprocess.check_output(
            ["terraform", "state", "show", "data.azion_intelligent_dns_zones.all_zones"],
            encoding="utf-8")

        #Extract zone_ids
        output_values = re.findall(r"zone_id\s+= (\d+)", state_output)

        for zone_id in output_values:
            self.zone_code += f'resource "azion_intelligent_dns_zone" "zone_{zone_id}" {{\n'
            self.zone_code += '  zone {\n'
            self.zone_code += f'    id = {zone_id}\n'
            self.zone_code += '  }\n'
            self.zone_code += '}\n\n'

            self.import_idns.append(
                f'terraform import azion_intelligent_dns_zone.zone_{zone_id} {zone_id}')

            self.zone_code += f'resource "azion_intelligent_dns_dnssec" "dnssec_{zone_id}" {{\n'
            self.zone_code += '  zone {\n'
            self.zone_code += f'    id = {zone_id}\n'
            self.zone_code += '  }\n'
            self.zone_code += '}\n\n'

            self.import_idns.append(
                f'terraform import azion_intelligent_dns_dnssec.dnssec_{zone_id} {zone_id}')

            state = f'data.azion_intelligent_dns_records.records["{zone_id}"]'
            records_output = subprocess.check_output(["terraform", "state", "show", state], encoding="utf-8")
            records_output = re.findall(r"record_id\s+= (\d+)", records_output)

            for record_id in records_output:
                self.records_code += f'resource "azion_intelligent_dns_record" "record_{record_id}" {{\n'
                self.records_code += f'  zone_id = {zone_id}\n'
                self.records_code += '}\n\n'

                self.import_idns.append(
                    f'terraform import azion_intelligent_dns_record.record_{record_id} {zone_id}/{record_id}')
        return len(output_values)

    def _save_terraform_config(self):
        with open(self.file_name+".tf", "w", encoding="utf-8") as file:
            file.write(constants.TERRAFORM_INITAL_CONTENT)
            file.write(self.zone_code)
            file.write(self.records_code)

    def create_early_state(self):

        util.delete_files_with_extension(["tf","sh","tfstate","backup"])

        self._terraform_mk_conf()
        #Remove intermediate state
        util.unlink_file("terraform.tfstate")
        self._init_context()

        if self._parse_state_output() > 0:
            has_zones = True
            self._save_terraform_config()
        else:
            has_zones = False
            print('no DNS zone found')

        #Remove intermediate terraform state
        util.unlink_file(f"{self.file_name}_tmp.tf")
        util.unlink_file("terraform.tfstate")
        return has_zones

    def create_finally_state(self):
        for cmd in self.import_idns:
            subprocess.run(cmd, shell=True, encoding="utf-8", stdout=subprocess.DEVNULL, check=False)
        
        util.delete_files_with_extension(["tf","sh","backup"])
