# With thanks to https://github.com/ryanlovett/jupyter-shiny-proxy/

import os
import logging
from tempfile import NamedTemporaryFile
import getpass
import subprocess

import click

class RShinyServerException(Exception):
    pass

def get_server_conf(command, port, app_init_timeout, app_idle_timeout, http_keepalive_timeout):
    return """

        run_as {user};

        app_init_timeout {app_init_timeout};
        app_idle_timeout {app_idle_timeout};
        http_keepalive_timeout {http_keepalive_timeout};
        
        preserve_logs true;
        
        server {{
            listen {port};
            location / {{
                app_dir {site_dir};
                log_dir {site_dir}/logs;
                bookmark_state_dir {site_dir}/bookmarks;
                directory_index on;
            }}
        }}

    """.format(
        user=getpass.getuser(),
        app_init_timeout= str(app_init_timeout),
        app_idle_timeout=str(app_idle_timeout),
        http_keepalive_timeout=str(http_keepalive_timeout),
        port=str(port),
        site_dir=command,

    )

@click.command()
@click.option('--port', default=8888, type=click.INT, help='port for the proxy server to listen on')
@click.option('--ip', default=None, help='Address to listen on')
@click.option('--debug/--no-debug', default=False, help='To display debug level logs')
@click.option('--app-init-timeout', default=60, type=click.INT, help='Defines the amount of time Shiny Server will wait for an R process to start before giving up. Defaults to 60 seconds')
@click.option('--app-idle-timeout', default=5, type=click.INT, help='Defines the amount of time an R process will persist with no connections before being terminated. Defaults to 5 seconds. Set to 0 to disable')
@click.option('--http-keepalive-timeout', default=45, type=click.INT, help='Defines how long a keepalive connection will sit between HTTP requests/responses before it is closed. Defaults to 45 seconds')
@click.argument('command', nargs=1, required=True)
def run(port, ip, debug, app_init_timeout, app_idle_timeout, http_keepalive_timeout, command):

    if debug:
        print('Setting debug')


    # Command can be absolute, or could be relative to cwd
    app_r_path = os.path.join(os.getcwd(), command)

    print("Fetching R Shiny folder {}".format(app_r_path))

    if os.path.isdir(app_r_path):
        print("CWD to {}".format(app_r_path))
        os.chdir(app_r_path)

    with NamedTemporaryFile(mode='w', delete=False) as conf_file:

        conf_str = get_server_conf(app_r_path, port, app_init_timeout, app_idle_timeout, http_keepalive_timeout )

        conf_file.write(conf_str)

        conf_file.close()

        subprocess.run(['shiny-server', conf_file.name])

        os.unlink(conf_file.name)
     
    
if __name__ == '__main__':

    try:

        run()

    except SystemExit as se:
        print('Caught SystemExit {}'.format(se))
