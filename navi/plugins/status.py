import click
from .api_wrapper import request_data
from .error_msg import error_msg


@click.command(help="Get Scan Status")
@click.argument('Scan_id')
def status(scan_id):
    try:
        data = request_data('GET', '/scans/'+str(scan_id) + '/latest-status')
        click.echo("\nLast Status update : {}".format(data['status']))
        click.echo()
    except Exception as E:
        error_msg(E)
