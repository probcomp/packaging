import os
import subprocess

def run(cmd):
  print cmd
  subprocess.check_call(cmd, shell=True)

def outputof(cmd, **kwargs):
  print cmd
  output = subprocess.check_output(cmd, **kwargs)
  print "OUTPUT:", output
  return output

def venv_run(venv_dir, cmd):
  os.chdir(venv_dir)
  print cmd
  subprocess.check_call('source %s/bin/activate; %s' % (venv_dir, cmd),
                        shell=True)

def shellquote(s):
  """Return `s`, quoted appropriately for use in a shell script."""
  return "'" + s.replace("'", "'\\''") + "'"
