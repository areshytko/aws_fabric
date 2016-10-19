
from fabric.api import *
from fabric.contrib.project import rsync_project


@task
def rsync(rdir='~', exclude=['fabfile.py', env.hosts_file, 'config.json', 'specification.json']):
    rsync_project(remote_dir=rdir, exclude=exclude)

__all__ = ["rsync"]
