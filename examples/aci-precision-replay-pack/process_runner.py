# CI-14 clean: subprocess without shell=True
import subprocess


def run_command(command_parts):
    subprocess.run(command_parts, check=False)
