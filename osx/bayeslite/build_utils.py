import os
import subprocess
import sys

def echo(*message):
  print >>sys.stderr, *message

def run(cmd):
  echo(cmd)
  subprocess.check_call(cmd, shell=True, stderr=sys.stderr)

def outputof(cmd, **kwargs):
  echo(cmd)
  output = subprocess.check_output(cmd, stderr=sys.stderr, **kwargs)
  echo("OUTPUT:", output)
  return output

def venv_run(venv_dir, cmd):
  os.chdir(venv_dir)
  echo(cmd)
  subprocess.check_call('source %s/bin/activate; %s' % (venv_dir, cmd),
                        shell=True, stderr=sys.stderr)

def shellquote(s):
  """Return `s`, quoted appropriately for use in a shell script."""
  return "'" + s.replace("'", "'\\''") + "'"
