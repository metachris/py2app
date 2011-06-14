def _emulate_shell_environ():
    import os
    import sys
    import time
    import subprocess

    if sys.version_info[0] > 2:
        env = os.environb
        split_char = '='.encode('ascii')
    else:
        env = os.environ
        split_char = '='

    # Start 'login -qf $LOGIN' in a pseudo-tty. The pseudo-tty
    # is required to get the right behavior from the shell, without
    # a tty the shell won't properly initialize the environment.
    master, slave = os.openpty()
    pid = os.fork()
    if pid == 0:
        # Child
        os.close(master)
        os.setsid()
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        os.execv('/usr/bin/login', ['login', '-qf', os.getlogin()])
        os._exit(42)

    else:
        # Parent
        os.close(slave)
        # Echo markers around the actual output of env, that makes it
        # easier to find the real data between other data printed
        # by the shell.
        os.write(master, 'echo "---------";env;echo "-----------"\r\n')
        os.write(master, 'exit\r\n')
        time.sleep(1)

        data = []
        b = os.read(master, 2048)
        while b:
            data.append(b)
            b = os.read(master, 2048)
        data = ''.join(data)
        os.waitpid(pid, 0)

    in_data = False
    for ln in data.splitlines():
        if not in_data:
            if ln.strip().startswith('--------'):
                in_data = True
            continue
        
        if ln.startswith('--------'):
            break

        try:
            key, value = ln.rstrip().split(split_char, 1)
        except:
            pass

        else:
            env[key] = value
        

_emulate_shell_environ()