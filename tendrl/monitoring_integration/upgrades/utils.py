import grp
import os
import pwd


def stop_service(service):
    os.system("systemctl stop %s" % service)


def start_service(service):
    os.system("systemctl start %s" % service)


def command_exec(cmd):
    os.system(cmd)


def remove_file(path):
    try:
        os.remove("/var/lib/graphite-web/graphite.db")
    except OSError as ex:
        print (ex)


def change_owner(path, owner, recursive=False):
    uid = pwd.getpwnam(owner).pw_uid
    gid = grp.getgrnam(owner).gr_gid
    _chown(path, uid, gid, recursive)


def _chown(path, uid, gid, recursive):
    os.chown(path, uid, gid)
    if recursive:
        for item in os.listdir(path):
            itempath = os.path.join(path, item)
            if os.path.isfile(itempath):
                os.chown(itempath, uid, gid)
            elif os.path.isdir(itempath):
                os.chown(itempath, uid, gid)
                _chown(itempath, uid, gid, recursive)
