import os
import subprocess
import glob
import genconf
import genstate

def delete_files_with_extension(extensions):
    # Encontra os arquivos com a extensão desejada
    for extension in extensions:
        files = glob.glob(f"*.{extension}")

        # Exclui os arquivos encontrados
        for file in files:
            os.remove(file)

#--------------------------------------------

TOKEN = os.getenv("AZION_API_TOKEN")
if TOKEN is None:
    print("Please, execute export AZION_API_TOKEN=<token>")
    exit(1)

delete_files_with_extension(["tf","sh","tfstate","backup"])

print("> Terraform State: Extrating iDNS Zones and Records...")
generator = genstate.TerraformStateGenerator("intermediate")
generator.create_state_generator()
print("> Terraform State: Extration done")

print("> Terraform State: Creating Terraform State...")
subprocess.run(["./intermediate.sh"], shell=True, encoding="utf-8", stdout=subprocess.DEVNULL)
generator.teardown()
print("> Terraform State: Done")

print("> Terraform Config: Creating Terraform Config...")
conf = genconf.TerraformGenConfig("terraform.tf")
conf.generate_terraform_config()
print("> Terraform Config: Done")