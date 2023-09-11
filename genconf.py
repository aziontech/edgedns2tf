import json
import subprocess
import os
import shutil
import constants
import util


class TerraformGenConfig:
    def __init__(self, output_file):
        self.output_file = output_file
        self.json_output = None
        self.config_content = {}

    def _parse_terraform_state(self):
        output = subprocess.check_output(["terraform", "show", "-json"], encoding="utf-8")
        self.json_output = json.loads(output)

    def _find_zone_resource_name(self,zone_id):
        for resource_name in self.config_content:
            if zone_id in resource_name:
                return resource_name
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

                zone_id = resource_values["zone_id"]
                zone_resource_name = self._find_zone_resource_name(zone_id)
                if zone_resource_name is None:
                    print("WARNING: could not find a resource for the zone {} when importing its DNSSEC, which will be skipped!".format(zone_id))
                    continue

                content = f'resource "{resource_type}" "{resource_name}" {{\n'
                content += f'    zone_id        = azion_intelligent_dns_zone.{zone_resource_name}.id\n'
                content += '    dns_sec = {\n'
                content += f'        is_enabled   = {str(resource_values["dns_sec"]["is_enabled"]).lower()}\n'
                content += '    }\n'
                content += '}\n\n'

                self.config_content[zone_resource_name] += content

            if resource_type == "azion_intelligent_dns_record":

                zone_id = resource_values["zone_id"]
                zone_resource_name = self._find_zone_resource_name(zone_id)
                if zone_resource_name is None:
                    print("WARNING: could not find a resource for the zone {} when importing its record {}, which will be skipped!".format(zone_id, resource_values["record"]["id"]))
                    continue

                content = f'resource "{resource_type}" "{resource_name}" {{\n'
                content += f'    zone_id        = azion_intelligent_dns_zone.{zone_resource_name}.id\n'
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

                self.config_content[zone_resource_name] += content

    def _save_terraform_conf(self):
        for name in self.config_content:
            with open(f'{name}.tf', "w", encoding="utf-8") as file:
                file.write(self.config_content[name])

    def _format_terraform_conf(self):
        fmt_output = subprocess.run(["terraform", "fmt", "-recursive", constants.OUTPUT_PATH], encoding="utf-8", stdout=subprocess.DEVNULL)
        if fmt_output.returncode != 0:
            print(f"WARNING: Failed to format the .tf files, fmt returned with status code {fmt_output.returncode}")

    def generate_terraform_config(self):

        #Prepare output folder
        try:
            if not os.path.exists(constants.OUTPUT_PATH):
                os.mkdir(constants.OUTPUT_PATH)
            else:
                shutil.rmtree(constants.OUTPUT_PATH)
                os.mkdir(constants.OUTPUT_PATH)
        except OSError as err:
            print(f"Unexpected {err=}, {type(err)=}")
            os.exit(1)

        self._parse_terraform_state()
        self._generate_terraform_content()
        self._save_terraform_conf()

        #Move conf files to output folder
        pwd = os.getcwd()
        try:
            for file in os.listdir(pwd):
                if os.path.splitext(file)[-1] == '.tf':
                    shutil.move(os.path.join(pwd, file), constants.OUTPUT_PATH)

            shutil.move(f'{pwd}/{constants.TF_STATE}', 
                        f'{constants.OUTPUT_PATH}/{constants.TF_STATE}')
            
            shutil.rmtree('.terraform')
            util.unlink_file(".terraform.lock.hcl")
        except OSError as err:
            print(f"Unexpected {err=}, {type(err)=}")
            os.exit(1)

        print("> Terraform Config: Formatting the generated .tf files")
        self._format_terraform_conf()

        print(f'> Terraform Config: Configuration available in the folder "{constants.OUTPUT_PATH}"')