import click
import time
from .api_wrapper import tenb_connection, navi_version
from .scanners import nessus_scanners
from .database import new_db_connection
from .error_msg import error_msg
from .licensed_count import get_licensed
from sqlite3 import Error
import textwrap


@click.command(help="Display or Print information found in Tenable.io")
@click.option('-scanners', is_flag=True, help="List all of the Scanners")
@click.option('-users', is_flag=True, help="List all of the Users")
@click.option('-exclusions', is_flag=True, help="List all Exclusions")
@click.option('-containers', is_flag=True, help="List all containers and their Vulnerability  Scores")
@click.option('-logs', is_flag=True, help="List The actor and the action in the log file")
@click.option('-running', is_flag=True, help="List the running Scans")
@click.option('-scans', is_flag=True, help="List all Scans")
@click.option('-nnm', is_flag=True, help="Nessus Network Monitor assets and their vulnerability scores")
@click.option('-assets', is_flag=True, help="Assets found in the last 30 days")
@click.option('-policies', is_flag=True, help="Scan Policies")
@click.option('-connectors', is_flag=True, help="List Connector Details and Status")
@click.option('-agroup', is_flag=True, help="List Access Groups and Status")
@click.option('-status', is_flag=True, help="Print T.io Status and Account info")
@click.option('-agents', is_flag=True, help="Print Agent information")
@click.option('-tgroup', is_flag=True, help='Print Target Groups')
@click.option('-licensed', is_flag=True, help='Print License information')
@click.option('-tags', is_flag=True, help='Print Tag Categories and values')
@click.option('-categories', is_flag=True, help='Print all of the Tag Categories and their UUIDs')
@click.option('-smtp', is_flag=True, help="Print your smtp information")
@click.option('-cloud', is_flag=True, help="Print Cloud assets found in the last 30 days by the connectors")
@click.option('-networks', is_flag=True, help="Print Network IDs")
@click.option('-version', is_flag=True, help="Display current version of Navi")
@click.option('-usergroup', is_flag=True, help="Display current User groups")
@click.option('--membership', default='', help="Display users of a certain group using the Group ID")
def display(scanners, users, exclusions, containers, logs, running, scans, nnm, assets, policies, connectors, agroup,
            status, agents, tgroup, licensed, tags, categories, smtp, cloud, networks, version, usergroup, membership):

    tio = tenb_connection()

    if scanners:
        nessus_scanners()

    if users:
        click.echo("\n{:34s} {:40s} {:40s} {:10s} {}".format("User Name", "Login Email", "UUID", "ID", "Enabled"))
        click.echo("-" * 150)
        for user in tio.users.list():
            click.echo("{:34s} {:40s} {:40s} {:10s} {}".format(str(user["name"]), str(user["username"]), str(user['uuid']), str(user['id']), str(user['enabled'])))
        click.echo()

    if exclusions:
        for exclusion in tio.exclusions.list():
            click.echo("\n{} {}".format("Exclusion Name :", exclusion["name"]))
            click.echo("-" * 150)
            click.echo("{}".format(str(exclusion["members"])))
        click.echo()

    if containers:
        # Use CS module
        resp = tio.get('container-security/api/v2/images?limit=1000')
        data = resp.json()
        click.echo("{:35s} {:35s} {:15s} {:15s} {:10s}".format("Container Name", "Repository ID", "Tag", "Docker ID", "# of Vulns"))
        click.echo("-" * 150)
        try:
            for images in data["items"]:
                click.echo("{:35s} {:35s} {:15s} {:15s} {:10s}".format(images["name"], images["repoName"], images["tag"], str(images["imageHash"]), str(images["numberOfVulns"])))
        except KeyError:
            pass
        click.echo()

    if logs:
        events = tio.audit_log.events()
        click.echo("{:24s} {:30s} {}".format("Event Date", "Action Taken", "User"))
        click.echo("-" * 150)
        for log in events:
            click.echo("{:24s} {:30s} {:30s}".format(str(log['received']), str(log['action']), str(log['actor']['name'])))
        click.echo()

    if running:
        click.echo("\n{:60s} {:10s} {:30s}".format("Scan Name", "Scan ID", "Status"))
        click.echo("-" * 150)
        for scan in tio.scans.list():
            if scan['status'] == "running":
                click.echo("{:60s} {:10s} {:30s}".format(str(scan['name']), str(scan['id']), str(scan['status'])))
        click.echo()

    if scans:
        click.echo("\n{:60s} {:10s} {:30s}".format("Scan Name", "Scan ID", "Status"))
        click.echo("-" * 150)
        for scan in tio.scans.list():
            click.echo("{:60s} {:10s} {:30s}".format(str(scan['name']), str(scan['id']), str(scan['status'])))
        click.echo()

    if nnm:
        for scan in tio.scans.list():
            if str(scan["type"]) == "pvs":
                resp = tio.get('scans/{}'.format(scan["id"]))
                data = resp.json()
                click.echo("\n{:20} {}".format("IP Address", "Score"))
                click.echo("-" * 150)
                for host in data["hosts"]:
                    click.echo("{:20} {}".format(str(host["hostname"]), str(host["score"])))
                click.echo()

    if assets:
        click.echo("\nBelow are the assets found in the last 30 days")
        click.echo("\n{:36} {:65} {:15} {}".format("IP Address(es)", "FQDN(s)", "Exposure Score", "Sources"))
        click.echo("-" * 150)
        for asset in tio.workbenches.assets():
            sources = []
            for source in asset["sources"]:
                sources.append(source['name'])
            click.echo("\n{:36} {:65} {:15} {}".format(str(asset["ipv4"]), str(asset["fqdn"]), str(asset["exposure_score"]), sources))
        click.echo()

    if policies:
        click.echo("\n{:40s} {:61s} {}".format("Policy Name", "Description", "Template ID"))
        click.echo("-" * 150)
        for policy in tio.policies.list():
            click.echo("{:40s} {:61s} {}".format(str(policy['name']), str(policy['description']), policy['template_uuid']))
        click.echo()

    if connectors:
        resp = tio.get('settings/connectors')
        data = resp.json()
        click.echo("\n{:11s} {:40s} {:40s} {:30s} {}".format("Type", "Connector Name", "Connector ID", "Last Sync", "Schedule"))
        click.echo("-" * 150)
        for conn in data["connectors"]:
            schedule = str(conn['schedule']['value']) + " " + str(conn['schedule']['units'])
            try:
                last_sync = conn['last_sync_time']
            except KeyError:
                last_sync = "Hasn't synced"
            click.echo("{:11s} {:40s} {:40s} {:30s} {}".format(str(conn['type']), str(conn['name']), str(conn['id']), last_sync, schedule))
        click.echo()

    if agroup:
        rules = "Not Rule Based"
        try:
            click.echo("\n{:25s} {:40s} {:25} {}".format("Group Name", "Group ID", "Last Updated", "Rules"))
            click.echo("-" * 150)
            for group in tio.access_groups.list():
                try:
                    updated = group['updated_at']
                except KeyError:
                    updated = "Not Updated"

                details = tio.access_groups.details(group['id'])
                try:
                    for rule in details['rules']:
                        rules = str(rule['terms'])
                except KeyError:
                    rules = "Not Rule Based"
                click.echo("{:25s} {:40s} {:25} {:60s}".format(str(group['name']), str(group['id']), str(updated), textwrap.shorten(rules, width=60)))
            click.echo()
        except Exception as E:
            error_msg(E)

    if status:
        try:
            data = tio.server.properties()
            session_data = tio.session.details()

            click.echo("\nTenable IO Information")
            click.echo("-" * 25)
            click.echo("{} {}".format("Container ID : ", session_data["container_id"]))
            click.echo("{} {}".format("Container UUID :", session_data["container_uuid"]))
            click.echo("{} {}".format("Container Name : ", session_data["container_name"]))
            click.echo("{} {}".format("Site ID :", data["analytics"]["site_id"]))
            click.echo("{} {}".format("Region : ", data["region"]))

            click.echo("\nLicense information")
            click.echo("-" * 25)
            click.echo("{} {}".format("Licensed Assets : ", get_licensed()))
            click.echo("{} {}".format("Agents Used : ", data["license"]["agents"]))
            click.echo("{} {}".format("Expiration Date : ", data["license"]["expiration_date"]))
            click.echo("{} {}".format("Scanners Used : ", data["license"]["scanners"]))
            click.echo("{} {}".format("Users : ", data["license"]["users"]))

            click.echo("\nEnabled Apps")
            click.echo("-" * 15)
            click.echo()
            for key in data["license"]["apps"]:
                click.echo(key)
                click.echo("-" * 5)
                try:
                    click.echo("{} {}".format("Expiration: ", str(data["license"]["apps"][key]["expiration_date"])))
                except KeyError:
                    pass
                click.echo("{} {}".format("Mode: ", str(data["license"]["apps"][key]["mode"])))
                click.echo()

        except Exception as E:
            error_msg(E)

    if agents:
        click.echo("\n{:46s} {:20} {:20} {:20} {:10} {}".format("Agent Name", "IP Address", "Last Connect Time", "Last Scanned Time", "Status", "Groups"))
        click.echo("-" * 150)

        for agent in tio.agents.list():
            last_connect = agent['last_connect']
            last_connect_time = time.strftime("%b %d %H:%M:%S", time.localtime(last_connect))

            try:
                last_scanned = agent['last_scanned']
                last_scanned_time = time.strftime("%b %d %H:%M:%S", time.localtime(last_scanned))
            except KeyError:
                # I assume if we can't pull as scanned time, it doesn't exist
                last_scanned_time = "Not Scanned"
            groups = ''
            try:
                for group in agent['groups']:
                    groups = groups + ", " + group['name']
            except KeyError:
                pass
            click.echo("{:46s} {:20s} {:20s} {:20s} {:10s} {}".format(str(agent['name']), str(agent['ip']),
                                                                      str(last_connect_time), str(last_scanned_time),
                                                                      str(agent['status']), str(groups[1:])))
        click.echo()

    if tgroup:
        print()
        print("*" * 40)
        print("Target Groups are going to be retired use the Migration script to covert them to tags")
        print("https://github.com/packetchaos/tio_automation/blob/master/migrate_target_groups.py")
        print("*" * 40)
        print("\nTarget Group Name".ljust(41), "TG ID".ljust(10), "Owner".ljust(30), "Members")
        print("-" * 100)
        for targets in tio.target_groups.list():
            mem = targets['members']
            print(str(targets['name']).ljust(40), str(targets['id']).ljust(10), str(targets['owner']).ljust(30), textwrap.shorten(mem, width=60))
        print()

    if licensed:
        click.echo("\n{} {}".format("Licensed Count: ", get_licensed()))
        click.echo()
        database = r"navi.db"
        conn = new_db_connection(database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT ip_address, fqdn, last_licensed_scan_date from assets where last_licensed_scan_date !=' ';")
            data = cur.fetchall()

            click.echo("{:20s} {:65s} {}".format("IP Address", "Full Qualified Domain Name", "Licensed Date"))
            click.echo("-" * 150)
            click.echo()
            for asset in data:
                ipv4 = asset[0]
                fqdn = asset[1]
                licensed_date = asset[2]
                # Don't display Web applications in this output
                if ipv4 != " ":
                    click.echo("{:20s} {:65s} {}".format(str(ipv4), str(fqdn), licensed_date))
        click.echo()

    if tags:
        click.echo("\n{:30s} {:35s} {}".format("Category", "  Value", "  Value UUID"))
        click.echo("-" * 150)
        for tag_values in tio.tags.list():
            try:
                tag_value = tag_values['value']
                uuid = tag_values['uuid']
            except KeyError:
                tag_value = "Value Not Set Yet"
                uuid = "NO Value set"
            click.echo("{:30s} : {:35s} {}".format(str(tag_values['category_name']), str(tag_value), str(uuid)))
        click.echo()

    if categories:
        click.echo("\n{:31s} {}".format("Tag Categories", "Category UUID"))
        click.echo("-" * 150)
        for cats in tio.tags.list_categories():
            category_name = cats['name']
            category_uuid = cats['uuid']
            click.echo("{:31s} {}".format(str(category_name), str(category_uuid)))
        click.echo()

    if smtp:
        try:
            database = r"navi.db"
            conn = new_db_connection(database)
            with conn:
                cur = conn.cursor()
                cur.execute("SELECT server, port, from_email from smtp;")
                data = cur.fetchall()
                for settings in data:
                    click.echo("\nYour email server: {}".format(settings[0]))
                    click.echo("The email port is: {}".format(settings[1]))
                    click.echo("Your email is: {}\n".format(settings[2]))
        except Error as E:
            click.echo("\nYou have no SMTP information saved.\n")
            click.echo("Error: ", E, "\n")

    if cloud:
        click.echo("\n{:11s} {:15s} {:45s} {:40} {}".format("Source", "IP", "FQDN", "UUID", "First seen"))
        click.echo("-" * 150)
        for assets in tio.workbenches.assets(('sources', 'set-has', 'AWS'), ('sources', 'set-has', 'GCP'), ('sources', 'set-has', 'AZURE'), filter_type="or", age=90):
            for source in assets['sources']:
                if source['name'] != 'NESSUS_SCAN':
                    asset_ip = assets['ipv4'][0]
                    uuid = assets['id']
                    try:
                        asset_fqdn = assets['fqdn'][0]
                    except IndexError:
                        asset_fqdn = "NO FQDN found"

                    click.echo("{:11s} {:15s} {:45s} {:40s} {}".format(str(source['name']), str(asset_ip),
                                                                       str(asset_fqdn), str(uuid),
                                                                       str(source['first_seen'])))
        click.echo()

    if networks:
        click.echo("\n{:20s} {:16} {}".format("Network Name", "# of Scanners", "UUID"))
        click.echo("-" * 150)
        for network in tio.networks.list():
            click.echo("{:20s} {:16} {}".format(str(network['name']), str(network['scanner_count']),
                                                str(network['uuid'])))
        click.echo()

    if version:
        click.echo("\nCurrent Navi Version: {}\n".format(navi_version()))

    if usergroup:
        click.echo("\n{:35s} {:10s} {:40s} {}".format("Group Name", "Group ID", "Group UUID", "User Count"))
        click.echo("-" * 150)
        for ugroup in tio.groups.list():
            click.echo("{:35s} {:10s} {:40s} {}".format(str(ugroup['name']), str(ugroup['id']),
                                                        str(ugroup['uuid']), str(ugroup['user_count'])))
        click.echo()

    if membership != '':
        click.echo("\n{:35s} {:40s} {:40s} {:10} {}".format("User Name", "Login email", "User UUID", "User ID",
                                                            "Enabled?"))
        click.echo("-" * 150)
        for user in tio.groups.list_users(membership):
            click.echo("{:35s} {:40s} {:40s} {:10} {}".format(str(user["name"]), str(user["username"]),
                                                              str(user['uuid']), str(user['id']),
                                                              str(user["enabled"])))
        click.echo()
