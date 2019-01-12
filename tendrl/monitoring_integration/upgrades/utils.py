import os


def print_message(message):
    print ("\n %s \n" % message)


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
        print_message(ex)
