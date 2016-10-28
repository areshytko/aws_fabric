
from fabric.api import *
from fabric.contrib.project import rsync_project
import subprocess


@task
def rsync(rdir='~', exclude=['fabfile.py', env.hosts_file, 'config.json', 'specification.json']):
    rsync_project(remote_dir=rdir, exclude=exclude)


@task
@runs_once
def notebook(lport=8000):
    """
    starts jupyter server and creates ssh port forwarding session for it
    @note: works only for a single host - the first one in the list of hosts
    :param lport: local port for the port forwarding
    """
    sudo("pip install jupyter")
    forward_session = subprocess.Popen('ssh -o "StrictHostKeyChecking no" -L {}:localhost:8888 {}@{}'.format(lport, env.user, env.host),
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
    local("xdg-open http://localhost:{}".format(lport))
    # run("jupyter notebook --no-browser") ----- this doesn't work by some reason


def kill_process_tree(pid):
    local("pkill -9 -P {}".format(pid))


def runbg(cmd, sockname="dtach"):
    return run('dtach -n `mktemp -u /tmp/%s.XXXX` %s'  % (sockname,cmd))


__all__ = ["rsync", "notebook"]
