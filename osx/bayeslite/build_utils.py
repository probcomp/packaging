import os
import subprocess
import sys

def run(cmd):
  print >>sys.stderr, cmd
  subprocess.check_call(cmd, shell=True, stderr=sys.stderr)

def outputof(cmd, **kwargs):
  print >>sys.stderr, cmd
  output = subprocess.check_output(cmd, **kwargs, stderr=sys.stderr)
  print "OUTPUT:", output
  return output

def venv_run(venv_dir, cmd):
  os.chdir(venv_dir)
  print >>sys.stderr, cmd
  subprocess.check_call('source %s/bin/activate; %s' % (venv_dir, cmd),
                        shell=True, stderr=sys.stderr)

def shellquote(s):
  """Return `s`, quoted appropriately for use in a shell script."""
  return "'" + s.replace("'", "'\\''") + "'"
