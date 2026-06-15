"""CI14_SUBPROCESS_SHELL_TRUE: subprocess invoked with shell=True."""
import subprocess


def run_cmd(cmd):
    subprocess.run(cmd, shell=True)
