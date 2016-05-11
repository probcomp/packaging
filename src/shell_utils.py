# -*- coding=utf-8 -*-

#   Copyright (c) 2010-2016, MIT Probabilistic Computing Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from __future__ import print_function
import re
import os
import subprocess
import sys
import StringIO

# For details on the choice to use /bin/sh and `.` rather than `source` below,
# despite virtualenv suggesting `source` in its user guide:
# https://virtualenv.pypa.io/en/latest/userguide.html
# see the comments on https://github.com/probcomp/packaging/commit/607740ba
SHELL_EXECUTABLE="/bin/sh"

def echo(*args, **kwargs):
  stdout=kwargs['stdout'] if 'stdout' in kwargs else sys.stdout
  # If we were doing unicode: args = map(shell_printf_quote, args)
  print(*args, file=stdout)

def run(cmd, stdout=sys.stdout, stderr=sys.stderr):
  echo(cmd, stdout=stdout)
  subprocess.check_call(cmd, shell=True, stdout=stdout, stderr=stderr,
                        executable=SHELL_EXECUTABLE)

def outputof(cmd, stderr=sys.stderr, **kwargs):
  echo(cmd)
  output = subprocess.check_output(cmd, stderr=stderr, shell=True,
                                   executable=SHELL_EXECUTABLE, **kwargs)
  echo("OUTPUT:", output)
  return output

def venv_run(venv_dir, cmd, stdout=sys.stdout, stderr=sys.stderr):
  os.chdir(venv_dir)
  echo(cmd, stdout)
  subprocess.check_call(
    '. %s/bin/activate; %s' % (shellquote(venv_dir), cmd),
    shell=True, stdout=stdout, stderr=stderr, executable=SHELL_EXECUTABLE)

def venv_outputof(venv_dir, cmd, stderr=sys.stderr):
  os.chdir(venv_dir)
  echo(cmd)
  output = subprocess.check_output(
    '. %s/bin/activate; %s' % (shellquote(venv_dir), cmd),
    shell=True, stderr=stderr, executable=SHELL_EXECUTABLE)
  echo("OUTPUT:", output)
  return output

def shellquote(s):
  """Return `s`, quoted appropriately for execution by a shell."""
  return "'" + re.sub(r'(?<![\'\"])\'(?![\'\"])', r"'\''",
                      re.sub(r"'\\''", "'\"'\\''\"'", s)) + "'"

def shell_printf_quote(s):
  """Return `s`, quoted in octal representation for shell printf's benefit.

  Note: This is intended to be interpretable by 'printf %s | bash -x'.
  """
  def convert(c):
    if re.search(r'[\w ]', c):
      return c
    else:
      strrep = oct(ord(c))
      i = len(strrep)
      result = ""
      while i > 0:
        i = i - 3
        result = "\\%3s%s" % (strrep[max(0, i):i+3], result)
      return re.sub(r'^\\000', '', re.sub(" ", "0", result))
  return ''.join(map(convert, s))

def check_python(python):
  # Note: some --python args won't work, bc eg python27 is a 32-bit version
  # that will produce a .app that osx will not open.
  # You get errors like:
  #    You can’t open the application “...” because PowerPC applications are no
  #    longer supported.
  # Or less helpfully:
  #    The application “...” can’t be opened.
  # and when investigating:
  #    lipo: can't figure out the architecture type of: ...
  # Instead, use the built-in python by not specifying anything, and get fine
  # results.
  # Rather than merely praying that the built-in python is
  # language-compatible, let's check.
  if python is None:
      python = "python"
  pyver = outputof('%s --version 2>&1' % (python,))
  assert "Python 2.7" == pyver[:10], \
    "Python versions >=2.7.9 and <3 are supported."
  if int(pyver[11:]) < 9:
      sys.stderr.write("WARNING: Python <2.7.9 not officially supported,"
                       " but trying anyway.\n")

def assert_equal(expected, observed, message=""):
  assert expected == observed, ("\n%r !=\n%r: %s" %
                                (expected, observed, message))

def test_shellquote():
  Abcodh = shellquote(u"A\x27b\x22c\xF5d\u03b7")
  assert_equal(u"'A'\\''b\"c\xf5d\u03b7'", Abcodh, "once")
  assert_equal(u"''\\''A'\"'\\''\"'b\"c\xf5d\u03b7'\\'''",
               shellquote(Abcodh), "twice")
  assert_equal(u"'before '\\''A'\"'\\''\"'b\"c\xf5d\u03b7'\\'''",
               shellquote("before %s" % Abcodh), "before")
  assert_equal(u"''\\''A'\"'\\''\"'b\"c\xf5d\u03b7'\\''after'",
               shellquote("%safter" % Abcodh), "after")

def test_shell_printf_quote():
  Abcodh = shell_printf_quote(u"A\x27b\x22c\xF5d\u03b7")
  assert_equal(u'A\\047b\\042c\\365d\\001\\667',
               Abcodh, "once")
  assert_equal(u'A\\134047b\\134042c\\134365d\\134001\\134667',
               shell_printf_quote(Abcodh), "twice")

test_shellquote()
test_shell_printf_quote()
