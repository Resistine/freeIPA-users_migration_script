import argparse
import json
import subprocess
from datetime import datetime
from ipalib import api
from ipalib.errors import CommandError, JSONError, PublicError

# authenticate user in freeIPA kerberos
def run_kinit(principal, password):
    try:
        subprocess.run(
            ['kinit', principal],
            input=password.encode(),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Kerberos ticket obtained successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error obtaining Kerberos ticket: {e.stderr.decode()}")
        return False
    return True

# create connection to api 
def connect_to_freeipa(server, principal, password):
    if not run_kinit(principal, password):
        return None

    try:
        api.bootstrap(host=server, context='cli')
        api.finalize()
        api.Backend.rpcclient.connect()
        return api
    except (CommandError, JSONError, PublicError) as e:
        print(f"Error connecting to FreeIPA: {e}")
        return None

# serialize all exported user data
def custom_serializer(obj):
    """Custom serializer for datetime and bytes objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    raise TypeError(f"Type {type(obj)} not serializable")

# export all users to json file specified by --file shell argument
def export_users(api, output_file):
    try:
        users = api.Command.user_find(all=True)['result']
        # Convert datetime and bytes objects to strings
        for user in users:
            for key, value in user.items():
                if isinstance(value, list):
                    user[key] = [custom_serializer(v) if isinstance(v, (datetime, bytes)) else v for v in value]
                elif isinstance(value, (datetime, bytes)):
                    user[key] = custom_serializer(value)
        with open(output_file, 'w') as f:
            json.dump(users, f, indent=4, default=custom_serializer)
        print(f"Users exported to {output_file}")
    except (CommandError, JSONError, PublicError) as e:
        print(f"Error exporting users: {e}")

# import json file to freeIPA server 
def import_users(api, input_file):
    try:
        with open(input_file, 'r') as f:
            users = json.load(f)

        for user in users:
            # Debugging the user data
            print(f"Processing user: {user}")

            required_fields = ['uid', 'givenname', 'sn', 'mail']
            missing_fields = [field for field in required_fields if field not in user]
            if missing_fields:
                print(f"Skipping user {user.get('uid', 'Unknown')}: Missing fields {missing_fields}")
                continue

            # Ensure all fields are strings or lists of strings
            user_data = {
                'uid': user['uid'][0] if isinstance(user['uid'], list) and user['uid'] else user.get('uid', ''),
                'givenname': user['givenname'][0] if isinstance(user['givenname'], list) and user['givenname'] else user.get('givenname', ''),
                'sn': user['sn'][0] if isinstance(user['sn'], list) and user['sn'] else user.get('sn', ''),
                'mail': user['mail'][0] if isinstance(user['mail'], list) and user['mail'] else user.get('mail', ''),
                'homedirectory': user.get('homedirectory', ['/home/' + user['uid'][0]])[0] if isinstance(user.get('homedirectory'), list) and user['uid'] else '/home/' + user.get('uid', ''),
                'loginshell': user.get('loginshell', ['/usr/bin/bash'])[0] if isinstance(user.get('loginshell'), list) else '/usr/bin/bash'
            }
            try:
                api.Command.user_add(**user_data)
                print(f"User {user_data['uid']} added successfully.")
            except (CommandError, JSONError, PublicError) as e:
                print(f"Failed to add user {user_data['uid']}: {e}")

            # Import SSH keys if present
            ssh_keys = user.get('ipasshpubkey', [])
            if ssh_keys:
                for key in ssh_keys:
                    try:
                        api.Command.user_mod(user_data['uid'], ipasshpubkey=key)
                        print(f"SSH key added for user {user_data['uid']}.")
                    except (CommandError, JSONError, PublicError) as e:
                        print(f"Failed to add SSH key for user {user_data['uid']}: {e}")

    except Exception as e:
        print(f"Error importing users: {e}")


def main():
    # help 
    parser = argparse.ArgumentParser(description='Export or import users from/to FreeIPA.')
    parser.add_argument('action', choices=['export', 'import'], help='Action to perform: export or import')
    parser.add_argument('--server', required=True, help='FreeIPA server address')
    parser.add_argument('--principal', required=True, help='FreeIPA admin principal')
    parser.add_argument('--password', required=True, help='FreeIPA admin password')
    parser.add_argument('--file', required=True, help='File to export to or import from')
    
    args = parser.parse_args()

    # do the magic 
    api = connect_to_freeipa(args.server, args.principal, args.password)
    if not api:
        print("Failed to connect to FreeIPA. Exiting.")
        return

    if args.action == 'export':
        export_users(api, args.file)
    elif args.action == 'import':
        import_users(api, args.file)

    api.Backend.rpcclient.disconnect()

if __name__ == '__main__':
    main()
