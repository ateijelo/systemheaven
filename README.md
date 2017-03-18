## System Heaven

System Heaven is an easy and secure way of running subprocesses. It is more convenient that `subprocess`, particularly when pipes are involved. And it's more secure than `os.system` because it never uses a shell underneath and it's not vulnerable to [shell injections][shell-injection].

### The problems with *os.system*

While `os.system` is simple and convenient, it has several downsides:

* **Insecure:** As long as the command to execute is fixed, `os.system`, as its underlying call `system`, just works. But as soon as some part of it is variable, there's a risk of injection. Escaping helps, but it's a headache, and it'll break sooner or later.

* **Inconsistent:** The behavior of `os.system` depends of the underlying shell and the operating system it's running on.

* **Limited:** The standard output and error output of the command can not be captured with `os.system`. The return value of `os.system` is usually the exit status of the command, but it again depends of the operating system and the interpreter.

### The problem with *subprocess*

The `subprocess` module actually does its job rather well. It solves successfully the issues with `os.system` and even integrates the capabilites of `os.spawn` and the old `Popen`. Its main downside is that some things, particularly pipes, can get cumbersome very quickly.

For instance, these shell backquotes:

~~~bash
output=`dmesg | grep hda`
~~~

become the following:

~~~python
from subprocess import Popen, PIPE
p1 = Popen(["dmesg"], stdout=PIPE)
p2 = Popen(["grep", "hda"], stdin=p1.stdout, stdout=PIPE)
p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
output = p2.communicate()[0]
~~~

### The way of System Heaven

The core of System Heaven is the fuction `sh`. The name of the function, and of the library, is intentionally based on that of the common Unix shells. But System Heaven's `sh` is not a shell, nor it ever uses one underneath.

The most basic call looks like this:

~~~python
from systemheaven import sh
sh("wget http://example.com/something.zip")
~~~

We can, however, use variables, which add flexibility while avoiding shell injections:

~~~python
sh("wget $url", url="http://example.com/something.zip")
~~~

You may wonder why isn't that just as vulnerable to injections as `os.system`. The difference stems from the fact that System Heaven does an intentionally limited parsing of its command line and variables become **one single element** of the list that is passed to `Popen`.

Even if a variable has spaces or other characters that would be special to a shell, it's safe to use it with System Heaven:

~~~python
dir = "Some Docs ; rm -rf /"
sh("ls -l $dir", dir=dir) # totally safe
~~~

That would produce, at worst, a *No such file or directory* from `ls`. This behavior is similar to what module `sqlite3` does with the question marks to avoid SQL injections.

A variable can become more than one argument if, instead of a string, you pass an iterable. For instance:

~~~python
sh("sha256sum $files", files=["file1.iso", "file2.iso"])
~~~

or better:

~~~python
from glob import glob
sh("sha256sum $files", files=glob("*.iso"))
~~~

Pipelines can be built very easily with `|`:

~~~python
sh("ls $dir | grep txt", dir="/home/user")
~~~

The longer the pipeline, the better it feels to use `sh`:

~~~python
sh("ls dir | grep a | grep b | grep c")
~~~

If you want to read the output of a command, put a `|` at the end:

~~~python
count = sh("ls | wc -l |").stdout.read()
~~~

With this capability, the pipe of the previous section becomes:

~~~python
output = sh('dmesg | grep hda |').stdout.read()
~~~

To send input to a command, put the `|` in front of the line:

~~~python
cmd = sh('| grep py$')
for filename in os.listdir():
    cmd.stdin.write(filename.encode('utf8'))
~~~

You can put `|` in both the beginning and the end of the line. But be careful of potential deadlocks.

Some design choices were driven by this goal. In particular, System Heaven avoids any string manipulation, as explained in the next sections.

### Quoting & Escaping

There are *no* quoting mechanisms in System Heaven. Neither `"`, nor `'`, nor `\` have any special meaning. Anywhere you feel inclined to use quoting or escaping, use a variable.

For instance, if you say:

~~~python
sh('ls -l "Some Documents"') # may not do what you're thinking
~~~

that will become something like:

~~~python
subprocess.Popen(['ls', '-l', '"Some', 'Documents"'], ...)
~~~

and you will be asking `ls` to list **two** directories: `"Some` and `Documents"`. Probably not what you originally meant. A similar thing would happend with `ls -l Some\ Documents`. That would list two directories, the first one of which happens to end with a backslash.

In any of those cases, say the following instead:

~~~python
sh('ls -l $dir', dir='Some Documents')
~~~

### Variables

Variables only work when used as a whole word. That means that a `$` sign in the middle or the end of a word will be passed untouched to the subprocess. For instance, the following:

~~~python
sh('ls -l /media/$user', user="ubuntu") # won't do what it seems
~~~

will become:

~~~python
subprocess.call(['ls', '-l', '/media/$user'])
~~~

and the `user` argument will just go unused.

Similarly there's no `${var}` syntax. You could use it, but then your *kwargs* would need a `"{var}"` key. System Heaven's parsing is intentionally limited and transparent: a variable is a word that starts with `$` and the rest of the word is the name of the variable --without restrictions-- and will be looked up, untouched, in *kwargs*.

The right way to do the thing above is:

~~~python
sh('ls -l $dir', dir="/media/" + user)
~~~

String manipulation is the responsibility of the caller.

### Special Variables

Some keyword arguments, like `_cwd` and `_env` are reserved for tweaking the behavior of `sh`. Avoid using variables starting with `_`.

### Examples

* The following Bash pipeline:

  ~~~bash
  #!/bin/bash
  count=$(ls | wc -l)
  ~~~

  would become this System Heaven invocation:

  ~~~python
  #!/usr/bin/env python3
  count = sh("ls | wc -l |").stdout.read()
  ~~~

* System Heaven variables can be iterables. This Bash line:

  ~~~bash
  #!/bin/bash
  count=$(ls *.txt | wc -l)
  ~~~

  becomes

  ~~~python
  #!/usr/bin/env python3
  from glob import glob
  count = sh("ls $files | wc -l |", files=glob("*.txt")).stdout.read()
  ~~~

* You can change the current working directory with `_cwd`. This Bash line:

  ~~~bash
  #!/bin/bash
  cd /home/user
  count=$(ls *.txt | wc -l)
  ~~~

  becomes:

  ~~~python
  #!/usr/bin/env python3
  from glob import glob
  count = sh("ls $files | wc -l |",
             files=glob("*.txt"),
             _cwd="/home/user"
          ).stdout.read()
  ~~~

[shell-injection]: https://en.wikipedia.org/wiki/Shell_injection#Shell_injection
