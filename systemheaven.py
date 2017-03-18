# -*- coding: utf8 -*-

"""
A shell-like and secure way of using subprocesses
"""

from subprocess import Popen, PIPE
import sys

def expandvars(words, kwargs):
    """expands words in the format $var
       to the value of "var" in kwargs,
       or to the empty string if not found"""
    newwords = []
    for word in words:
        if word.startswith("$"):
            value = kwargs.get(word[1:], "")
            if isinstance(value, str):
                newwords.append(value)
            else:
                newwords.extend(value)
        else:
            newwords.append(word)
    return newwords

class Pipeline():
    """Wraps a number of subprocesses"""

    def __init__(self, procs):
        self.procs = procs
        self.stdin = procs[0].stdin
        self.stdout = procs[-1].stdout

    def wait(self):
        "waits for all processes"
        for proc in self.procs:
            proc.wait()
        return self.returncode

    @property
    def ok(self):
        """waits and returns True if returncode is 0"""
        ret = self.wait()
        return ret == 0

    @property
    def returncode(self):
        "returns last process' returncode"
        return self.procs[-1].returncode

def sh(pipeline: str, **kwargs):
    # pylint: disable=C0103
    """
    pipeline: str A sequence of commands to be run separated by
                  zero or more | characters, with optional
                  variables in $var form
    kwargs: dict  Values for the variables in command. Missing
                  variables will become empty-string arguments.
                  Avoid using variable names starting with "_"
                  for they may be reserved.
    """
    commands = pipeline.split("|")

    procs = []
    headpipe = False
    tailpipe = False

    for i, command in enumerate(commands):
        words = command.split()
        if len(words) == 0:
            if i == 0:
                headpipe = True
            elif i == len(commands) - 1:
                tailpipe = True
            else:
                print("WARNING: SystemHeaven interprets consecutive pipes " +
                      "(||) as a single one", file=sys.stderr)
            continue

        words = expandvars(words, kwargs)
        stdout = None
        stdin = None
        if headpipe and len(procs) == 0:
            stdin = PIPE
        if len(procs) > 0:
            stdin = procs[-1].stdout
        if i < len(commands) - 1:
            stdout = PIPE

        proc = Popen(
            words,
            stdin=stdin,
            stdout=stdout,
            cwd=kwargs.get("_cwd", None),
            env=kwargs.get("_env", None),
        )
        procs.append(proc)

    if headpipe or tailpipe:
        return Pipeline(procs)

    for proc in procs:
        proc.wait()
    return procs[-1].returncode
