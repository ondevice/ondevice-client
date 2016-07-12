"""
{cmd} services
  - lists local services
{cmd} services add  [-h/--hidden] <protocol> <name> [parameters]
  - adds a (hidden) service with the given protocol, name and parameters
{cmd} services rm <name> [-f/--force]
  - removes a service (by name)

The default installation only has the 'ssh' 'echo' service enabled.

Parameters:
- `--hidden`

Examples:

$ {cmd} services
Proto   Name    Params
ssh     ssh     --port=378
echo    [echo]

$ {cmd} services rm echo -f
$ {cmd} services add echo otherEcho --hidden
"""

from ondevice.core import service

def addService(name, protocol):
    # TODO parse additional arguments ('--hidden', ...)
    service.add(name, protocol)

def listServices():
    for name, info in service.listServices().items():
        details = ['protocol={0}'.format(info['protocol'])]
        if 'hidden' in info and info['hidden'] == True:
            details.append('HIDDEN')
        print('{0}\t{1}'.format(name, ', '.join(details)))

def rmService(name):
    service.remove(name)

def run(subcmd='list', *args):
    if subcmd == 'list':
        listServices(*args)
    elif subcmd == 'add':
        addService(*args)
    elif subcmd == 'rm':
        rmService(*args)
    else:
        raise Exception("Unsupported subcommand: {0}".format(subcmd))

def usage():
    return "[add/rm] [args...]", "Manages services"
