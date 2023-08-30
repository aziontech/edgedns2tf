import json
import subprocess
import os
import shutil
import constants


class TerraformGenConfig:
    def __init__(self, output_file):
        self.output_file = output_file
        self.json_output = None
        self.config_content = {}

    def _parse_terraform_state(self):
        output = subprocess.check_output(["terraform", "show", "-json"], encoding="utf-8")
        self.json_output = json.loads(output)

    def _find_zone(self,zone_id):
        for zone in self.config_content:
            if zone_id in zone:
                return zone
        return None

    def _generate_terraform_content(self):

        self.config_content["provider"] = constants.TERRAFORM_INITAL_CONTENT

        #Process the the zones first
        for resource in self.json_output["values"]["root_module"]["resources"]:
            resource_type = resource["type"]
            resource_name = resource["name"]
            resource_values = resource["values"]

            if resource_type == "azion_intelligent_dns_zone":
                content = f'resource "{resource_type}" "{resource_name}" {{\n'
                content += '    zone = {\n'
                content += f'        domain      = "{resource_values["zone"]["domain"]}"\n'
                content += f'        is_active   = {str(resource_values["zone"]["is_active"]).lower()}\n'
                content += f'        name        = "{resource_values["zone"]["name"]}"\n'
                content += '    }\n'
                content += '}\n\n'

                self.config_content[resource_name] = content

        #After process the record and dnssec resources
        for resource in self.json_output["values"]["root_module"]["resources"]:
            resource_type = resource["type"]
            resource_name = resource["name"]
            resource_values = resource["values"]

            if resource_type == "azion_intelligent_dns_zone":
                continue

            if resource_type == "azion_intelligent_dns_dnssec":

                zone_name = self._find_zone(resource_values["zone_id"])
                if zone_name is not None:
                    content = f'resource "{resource_type}" "{resource_name}" {{\n'
                    content += f'    zone_id        = "{resource_values["zone_id"]}"\n'
                    content += '    dns_sec = {\n'
                    content += f'        is_enabled   = {str(resource_values["dns_sec"]["is_enabled"]).lower()}\n'
                    content += '    }\n'
                    content += '}\n\n'

                    self.config_content[zone_name] += content

            if resource_type == "azion_intelligent_dns_record":

                zone_name = self._find_zone(resource_values["zone_id"])
                if zone_name is not None:
                    content = f'resource "{resource_type}" "{resource_name}" {{\n'
                    content += f'    zone_id        = "{resource_values["zone_id"]}"\n'
                    content += '    record = {\n'
                    content += '        answers_list = [\n'
                    for answer in resource_values["record"]["answers_list"]:
                        content += f'            "{answer}",\n'
                    content += '        ]\n'
                    if resource_values["record"]["description"] is not None:
                        content += f'        description  = "{resource_values["record"]["description"]}"\n'
                    content += f'        entry        = "{resource_values["record"]["entry"]}"\n'
                    content += f'        policy       = "{resource_values["record"]["policy"]}"\n'
                    content += f'        record_type  = "{resource_values["record"]["record_type"]}"\n'
                    content += f'        ttl          = {resource_values["record"]["ttl"]}\n'
                    if resource_values["record"]["weight"] is not None:
                        content += f'        weight       = {resource_values["record"]["weight"]}\n'
                    content += '    }\n'
                    content += '}\n\n'

                    self.config_content[zone_name] += content

    def _save_terraform_conf(self):
        for name in self.config_content:
            with open(f'{name}.tf', "w", encoding="utf-8") as file:
                file.write(self.config_content[name])

    def generate_terraform_config(self):

        #Prepare output folder
        if not os.path.exists(constants.OUTPUT_PATH):
            os.mkdir(constants.OUTPUT_PATH)
        else:
            shutil.rmtree(constants.OUTPUT_PATH)
            os.mkdir(constants.OUTPUT_PATH)

        self._parse_terraform_state()
        self._generate_terraform_content()
        self._save_terraform_conf()

        #Move conf files to output folder
        pwd = os.getcwd()
        for file in os.listdir(pwd):
            if os.path.splitext(file)[-1] == '.tf':
                shutil.move(os.path.join(pwd, file), constants.OUTPUT_PATH)

        shutil.move(f'{pwd}/{constants.TF_STATE}', f'{constants.OUTPUT_PATH}/{constants.TF_STATE}')
