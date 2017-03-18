### System Heaven

System Heaven is a middle point between `system` and `execve`. Or, in more Pythonic terms, between `os.system` and `subprocess`.

#### The problems with `os.system`

While `os.system` is simple and convenient, it has several downsides:

* **Insecure:** As long as the command to execute is fixed, `os.system`, as its underlying call `system`, just works. But as soon as some part of it is variable, there's a risk of injection. Escaping helps, but it's a headache, and it'll break sooner or later.

* **Inconsistent:** The behaviour of `os.system` depends of the underlying shell and the operating system it's running on.

* **Limited:** The return value of `os.system` is usually the exit status of the command, but it again depends of the operating system and the interpreter. The standard output and error output of the command can not be captured with `os.system`.

#### The problem with `subprocess`

The `subprocess` module doesn't really have any problem. It solves successfully the issues with `os.system` and even integrates the capabilites of `os.spawn` and the old `Popen`. The only downside is that what used to be simple can now become complex, as its documentation shows with this example:

This shell backquotes:

~~~bash
output=`dmesg | grep hda`
~~~

now become:

~~~python
from subprocess import Popen, PIPE
p1 = Popen(["dmesg"], stdout=PIPE)
p2 = Popen(["grep", "hda"], stdin=p1.stdout, stdout=PIPE)
p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
output = p2.communicate()[0]
~~~

#### The way of System Heaven

Using System Heaven, that last snippet becomes this:

~~~python
from systemheaven import sh
output = sh('dmesg | grep hda').read()
~~~
