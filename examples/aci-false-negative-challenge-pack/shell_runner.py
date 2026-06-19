# CI-14 fixture: subprocess shell=True
import subprocess


def run_command(command):
    subprocess.run(command, shell=True)
