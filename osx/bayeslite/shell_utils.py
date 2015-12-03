# coding=utf-8

from __future__ import print_function
import re
import os
import subprocess
import sys

def echo(*args):
  # If we were doing unicode: args = map(shell_printf_quote, args)
  print(*args, file=sys.stderr)

def run(cmd):
  echo(cmd)
  subprocess.check_call(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)

def outputof(cmd, **kwargs):
  echo(cmd)
  output = subprocess.check_output(cmd, stderr=sys.stderr, shell=True, **kwargs)
  echo("OUTPUT:", output)
  return output

def venv_run(venv_dir, cmd):
  os.chdir(venv_dir)
  echo(cmd)
  subprocess.check_call(
    'source %s/bin/activate; %s' % (shellquote(venv_dir), cmd),
    shell=True, stderr=sys.stderr)

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
