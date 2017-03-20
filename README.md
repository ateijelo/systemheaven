# System Heaven

System Heaven is an easy and secure way of running subprocesses. It is more convenient that `subprocess`, particularly when pipes are involved. And it's more secure than `os.system` because it never uses a shell underneath and it helps avoid [shell injections][shell-injection].

The name of the library and it's main function `sh` are intentionaly based of that of the common Unix shells, but System Heaven is not a shell.

## Quick Tour

### The Basics

Start by importing `sh`:

~~~python
from systemheaven import sh
~~~

To run a simple command, just do:

~~~python
sh('wget http://example.com/something.zip')
~~~

You can use variables to change parts of the line:

~~~python
sh('wget $url', url='http://example.com/something.zip')
~~~

and that's safe even if the value contains characters that would be special to a shell:

~~~python
url = 'http://example.com/ ; rm -rf /'
sh('wget $url', url=url) # totally safe
~~~

The snippet above shows how `sh` helps avoid shell injections. The `url` value becomes **one single element** of the list that gets to `Popen`. That `wget` may throw a *404 Not Found* error but there's no risk of running the `rm -rf` at the end.

If you build a string from Python values before passing it to `sh`, there's no way for System Heaven to help avoid injections. **Don't do this**. Use System Heaven's variables.

The value of a variable can be an iterable. In that case the command list is simply extended with the elements of the iterable. That allows code like the following:

~~~python
sh('md5sum $files', files=['file1.iso', 'file2.iso'])
~~~

or even better:

~~~python
from glob import glob
sh('md5sum $files', files=glob('*.iso'))
~~~

There are some special variables:

| Variable | Meaning               |
|----------|-----------------------|
| `_cwd`   | Change current dir    |
| `_env`   | Set a new environment |

Special variable all start with `_`. Avoid prefixing for your own variables with it.

### Pipelines

It's very easy to build pipelines with `sh`, just use `|`:

~~~python
sh('ls | grep pyc')
~~~

And while it looks like a shell, there's no shell involved. `sh` will create the two processes and connect the output of the first to the input of the second on its own. Under the hood, `sh` simply uses Python's `subprocess` module to achieve it in a simple & portable way.

If you want to read the output of the command, put a `|` at the end:

~~~python
cmd = sh('ls | grep pyc |')
for line in cmd.stdout:
  print(line)
~~~

Equivalently, you can send data to the subprocess by placing a `|` at the beginning:

~~~python
cmd = sh('| grep pyc')
for name in os.listdir(b'.'):
  cmd.stdin.write(name + b'\n')
~~~

When you don't use `|` at the beginning nor at the end, `sh` waits for the commands to complete. If you use one, though, `sh` returns right after building the pipeline so you can communicate with the subprocess.

You can wait for a command and check that it finished correctly with `.ok`:

~~~python
if sh('unzip somefile.zip').ok:
  print('Sucessfully extracted')
~~~

---

## The Design of System Heaven

System Heaven is designed to fill the gap that sometimes arises between shell scripts & Python when doing system tasks.

Shell languages are great at combining and connecting commands. But as soon as the processing of data gets complex, they become too restrictive. Think, for instance, of handling JSON. It's possible, but shell languages are the wrong tool for it.

Python, on the other hand, is much more expressive, but if the task at hand needs to use many external commands, tools like `os.system` and `subprocess` fall short.

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
p1 = Popen(['dmesg'], stdout=PIPE)
p2 = Popen(['grep', 'hda'], stdin=p1.stdout, stdout=PIPE)
p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
output = p2.communicate()[0]
~~~

### The way of System Heaven

System Heaven tries to fill this gap by giving the user the familiar syntax of the shell without compromising on security.

The `subprocess` snippet above becomes:

~~~python
output = sh('dmesg | grep hda |').stdout.read()
~~~

Under the hood, System Heaven uses precisely `subprocess` to build the pipeline.

### Quoting & Escaping

To avoid shell injections, System Heaven performs an intentionally limited parsing of the shell constructions it accepts, namely, pipes, variables & redirections.

There are, consequently, no escaping mechanisms in System Heaven. Neither the quotes (`"` and `'`) nor the backslash `\` have any special meaning for System Heaven.

A call like this:

~~~python
sh('ls -l "Some Documents"') # may not do what you're thinking
~~~

will become this:

~~~python
subprocess.Popen(['ls', '-l', '"Some', 'Documents"'], ...)
~~~

that is, `ls` will try to list **two** directories, `"Some` and `Documents"`.

Similarly, doing:

~~~python
sh('ls -l Some\ Documents')
~~~

will become:

~~~python
subprocess.Popen(['ls', '-l', 'Some\ Documents'], ...)
~~~

and since `'\ '` is not special to Python, `ls` will try to list a directory *with a backslash* in its name.

In both cases, you may have meant to do this:

~~~python
sh("ls -l $dir", dir="Some Documents")
~~~

and you don't have to worry about any kind of escaping.

### Variables

Variables only work when used as a whole word. That means that a `$` sign in the middle or the end of a word will be passed untouched to the subprocess. For instance, the following:

~~~python
sh('ls -l /media/$user', user="ubuntu") # won't do what it seems
~~~

will become:

~~~python
subprocess.Popen(['ls', '-l', '/media/$user'])
~~~

and the `user` argument will just go unused.

Similarly there's no `${var}` syntax. You could use it, but then your *kwargs* would need a `"{var}"` key. System Heaven's parsing is intentionally limited and transparent: a variable is a word that starts with `$` and the rest of the word is the name of the variable --without restrictions-- and will be looked up, untouched, in *kwargs*.

The right way to do the thing above is:

~~~python
sh('ls -l $dir', dir="/media/" + user)
~~~

String manipulation is the responsibility of the caller.


[shell-injection]: https://en.wikipedia.org/wiki/Shell_injection#Shell_injection
