import datetime 
import os
import subprocess  # nosec
import getpass
import argparse
import logging


class Backup:

    def __init__(self, database_name, database_user, type):
        timestr = datetime.datetime.now().strftime('%Y-%m-%d')
        self.filename = f'backup-{type}-{timestr}-{database_name}.dump'
        self.database_name = database_name
        self.database_user = database_user
        self.type = type
        self.password = None
        self.hostname_mysql = os.environ.get("HOSTNAME_MYSQL", "192.168.1.62")
        self.hostname_psql = os.environ.get("HOSTNAME_PSQL", "192.168.1.62")
        self.port_mysql = os.environ.get("PORT_MYSQL", "3306")
        self.port_psql = os.environ.get("PORT_PSQL","5432")

    def set_password(self):
        """
        Retrieve the database password from an environment variable.
        """
        self.password = os.environ.get("DB_PASSWORD")
        if not self.password:
            logging.warning("Database password not set. Please provide the DB_PASSWORD environment variable.")
            exit(1)

    def create_backup(self, type):
        """
        Create a backup of the database.
        """
        if type == "MYSQL":
            try:
                cmd = [
                    'mysqldump',
                    '--single-transaction',
                    '-u', self.database_user,
                    f'-p{self.password}',
                    '-h', self.hostname_mysql,
                    '-P', str(self.port_mysql),
                    '--no-tablespaces',
                    '-B', self.database_name,
                ]

                with open(self.filename, 'w') as backup_file:
                    result = subprocess.run(cmd, stdout=backup_file, check=True)  # nosec

                if result.returncode != 0:
                    logging.warning(f'Command failed. Return code: {result.returncode}')
                    exit(1)

                return self.filename

            except Exception as e:
                logging.warning(e)
                exit(1)

        elif type == "PSQL":
            try:
                cmd = [
                    'pg_dump',
                    '-U', self.database_user,
                    '-h', self.hostname_psql,
                    '-p', str(self.port_psql),
                    '-F', 'c',  
                    '-f', self.filename,
                    self.database_name
                ]

                result = subprocess.run(cmd, check=True)  # nosec

                if result.returncode != 0:
                    logging.warning(f'Command failed. Return code: {result.returncode}')
                    exit(1)

                return self.filename

            except Exception as e:
                logging.warning(e)
                exit(1)

    @staticmethod
    def delete_old_backups(directory, retention_days):
        """
        Deletes backup files older than the specified retention period.
        """
        now = datetime.datetime.now()
        for file in os.listdir(directory):
            if file.startswith("backup-") and file.endswith(".dump"):
                file_path = os.path.join(directory, file)
                file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                age = (now - file_mtime).days
                if age > retention_days:
                    try:
                        os.remove(file_path)
                        logging.info(f"Deleted old backup: {file_path}")
                    except Exception as e:
                        logging.warning(f"Failed to delete {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Execute a local backup of a database.")
    parser.add_argument("-dn", "--database_name", required=True, help="Enter the name of the database for the backup.")
    parser.add_argument("-du", "--database_user", required=True, help="Enter the username of the database for the backup.")
    parser.add_argument("-b", "--backup", action="store_true", help="Backup the database.")
    parser.add_argument("-t", "--type", choices=["MYSQL", "PSQL"], required=True, help="MYSQL or PSQL")
    parser.add_argument("-bd", "--backup_dir", default=".", help="Directory where backups are stored.")
    parser.add_argument("-r", "--retention", type=int, help="Retention period in days for keeping backups.")
    args = parser.parse_args()

    db_name = args.database_name
    db_user = args.database_user
    backup = args.backup
    type = args.type
    backup_dir = args.backup_dir
    retention = args.retention

    if backup:
        b = Backup(db_name, db_user, type)
        try:
            b.set_password()
            backup_file = b.create_backup(type=type)
        except Exception as e:
            logging.warning(e)
        else:
            print(f"Backup successful: {backup_file}")

    if retention:
        try:
            Backup.delete_old_backups(directory=backup_dir, retention_days=retention)
        except Exception as e:
            logging.warning(f"Failed to clean up old backups: {e}")


if __name__ == '__main__':
    main()
