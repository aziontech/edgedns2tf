import subprocess
import re
import os
import constants

class TerraformStateGenerator:
    def __init__(self, file_name):
        self.file_name = file_name
        self.zone_code = ""
        self.records_code = ""
        self.import_idns = "#!/bin/sh\n\nterraform init\n"

    def _terraform_mk_conf(self):
        with open(f"./{self.file_name}_tmp.tf", "w", encoding="utf-8") as file:
            file.write(constants.TERRAFORM_INITAL_CONTENT)
            file.write(constants.TERRAFORM_IDNS_DATA)

    def _terraform_unlink_file(self,file_name):
        if os.path.exists(file_name):
            os.remove(file_name)

    def _init_context(self):
        subprocess.run(["terraform", "init"], encoding="utf-8", stdout=subprocess.DEVNULL, check=False)
        subprocess.run(["terraform", "apply"], encoding="utf-8", stdout=subprocess.DEVNULL, check=False)

    def _parse_state_output(self):
        #Get the TF state data
        state_output = subprocess.check_output(
            ["terraform", "state", "show", "data.azion_intelligent_dns_zones.all_zones"], encoding="utf-8"
        )

        #Extract zone_ids
        output_values = re.findall(r"zone_id\s+= (\d+)", state_output)

        for zone_id in output_values:
            self.zone_code += f'resource "azion_intelligent_dns_zone" "zone_{zone_id}" {{\n'
            self.zone_code += '  zone {{\n'
            self.zone_code += f'    id = {zone_id}\n'
            self.zone_code += '  }}\n'
            self.zone_code += '}}\n\n'

            self.import_idns += f'terraform import azion_intelligent_dns_zone.zone_{zone_id} {zone_id}\n'

            self.zone_code += f'resource "azion_intelligent_dns_dnssec" "dnssec_{zone_id}" {{\n'
            self.zone_code += '  zone {{\n'
            self.zone_code += f'    id = {zone_id}\n'
            self.zone_code += '  }}\n'
            self.zone_code += '}}\n\n'

            self.import_idns += f'terraform import azion_intelligent_dns_dnssec.dnssec_{zone_id} {zone_id}\n'

            state = f'data.azion_intelligent_dns_records.records["{zone_id}"]'
            records_output = subprocess.check_output(["terraform", "state", "show", state], encoding="utf-8")
            records_output = re.findall(r"record_id\s+= (\d+)", records_output)

            for record_id in records_output:
                self.records_code += f'resource "azion_intelligent_dns_record" "record_{record_id}" {{\n'
                self.records_code += f'  zone_id = {zone_id}\n'
                self.records_code += '}}\n\n'

                self.import_idns += f'terraform import azion_intelligent_dns_record.record_{record_id} {zone_id}/{record_id}\n'

    def _save_terraform_config(self):
        with open(self.file_name+".tf", "w", encoding="utf-8") as file:
            file.write(constants.TERRAFORM_INITAL_CONTENT)
            file.write(self.zone_code)
            file.write(self.records_code)

        with open(self.file_name+".sh", "w", encoding="utf-8") as file:
            file.write(self.import_idns)

        os.chmod(self.file_name+".sh", 0o755)

    def create_state_generator(self):
        #prepare configs
        self.teardown()
        self._terraform_mk_conf()
        self._terraform_unlink_file("./terraform.tfstate")

        self._init_context()
        self._parse_state_output()
        self._save_terraform_config()

        #Remove intermediate terraform state
        self._terraform_unlink_file(f"./{self.file_name}_tmp.tf")
        self._terraform_unlink_file("./terraform.tfstate")

    def teardown(self):
        self._terraform_unlink_file(f"./{self.file_name}.tf")
        self._terraform_unlink_file(f"./{self.file_name}.sh")
