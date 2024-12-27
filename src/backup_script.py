import datetime
import os
import subprocess  # nosec
import argparse
import logging


class Backup:

    def __init__(self, database_name, database_user, type, backup_dir):
        timestr = datetime.datetime.now().strftime('%Y-%m-%d')
        self.filename = f'backup-{type}-{timestr}-{database_name}.dump'
        self.database_name = database_name
        self.database_user = database_user
        self.type = type
        self.password = None
        self.backup_dir = backup_dir
        self.hostname_mysql = os.environ.get("HOSTNAME_MYSQL", "192.168.1.62")
        self.hostname_psql = os.environ.get("HOSTNAME_PSQL", "192.168.1.62")
        self.port_mysql = os.environ.get("PORT_MYSQL", "3306")
        self.port_psql = os.environ.get("PORT_PSQL", "5432")

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
        # Ensure the backup directory exists
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        # Prepend the backup directory to the filename
        full_path = os.path.join(self.backup_dir, self.filename)

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

                with open(full_path, 'w') as backup_file:
                    result = subprocess.run(cmd, stdout=backup_file, check=True)  # nosec

                if result.returncode != 0:
                    logging.warning(f'Command failed. Return code: {result.returncode}')
                    exit(1)

                return full_path

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
                    '-f', full_path,
                    self.database_name
                ]

                result = subprocess.run(cmd, check=True)  # nosec

                if result.returncode != 0:
                    logging.warning(f'Command failed. Return code: {result.returncode}')
                    exit(1)

                return full_path

            except Exception as e:
                logging.warning(e)
                exit(1)

    @staticmethod
    def delete_old_backups(directory, retention_days):
        """
        Deletes backup files older than the specified retention period.
        """
        now = datetime.datetime.now()
        logging.info(f"Starting cleanup of backups in {directory} with retention period: {retention_days} days")
        for file in os.listdir(directory):
            if file.startswith("backup-") and file.endswith(".dump"):
                file_path = os.path.join(directory, file)
                file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                age = (now - file_mtime).days
                logging.info(f"Checking file {file_path}: age = {age} days")
                if age >= retention_days:
                    try:
                        os.remove(file_path)
                        logging.info(f"Deleted old backup: {file_path}")
                    except Exception as e:
                        logging.warning(f"Failed to delete {file_path}: {e}")
                else:
                    logging.info(f"File {file_path} is not old enough to delete (age = {age} days).")


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

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
        b = Backup(db_name, db_user, type, backup_dir)
        try:
            b.set_password()
            backup_file = b.create_backup(type=type)
        except Exception as e:
            logging.warning(e)
        else:
            logging.info(f"Backup successful: {backup_file}")

    if retention is not None:
        try:
            Backup.delete_old_backups(directory=backup_dir, retention_days=retention)
            logging.info(f"Old backups older than {retention} days were successfully deleted from {backup_dir}.")
        except Exception as e:
            logging.warning(f"Failed to clean up old backups: {e}")


if __name__ == '__main__':
    main()