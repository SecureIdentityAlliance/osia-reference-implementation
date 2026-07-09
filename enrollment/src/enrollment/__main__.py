
import sys
import os
import json
import time
import logging
import logging.handlers
import configargparse

import enrollment
import enrollment.server
import enrollment.model

# [---CUSTO---]
# Additional imports/global vars
# [---CUSTO---]

# _____________________________________________________________________________
class FormatterJSON(logging.Formatter):
    """
    Custom logging formatter to format as JSON the logs
    """
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        s = time.strftime("%Y-%m-%dT%H:%M:%S", ct)
        s = '%s.%03d' % (s, record.msecs)
        s += time.strftime("%z", ct)
        return s

    def format(self, record):
        d = dict()
        d['timestamp'] = self.formatTime(record)
        d['logger'] = record.name
        d['thread'] = record.threadName
        d['level'] = record.levelname
        d['message'] = record.getMessage()
        if 'transactionId' in record.__dict__:
            d['transactionId'] = record.transactionId
        # [---CUSTO---]
        # Customization of log content
        # [---CUSTO---]
        s = ''
        if record.exc_info and not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if not s.endswith("\n"):
                s = s + "\n"
            s = s + record.exc_text
        if record.stack_info:
            if not s.endswith("\n"):
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)
        if s:
            d['stack_trace'] = s
        return json.dumps(d)

# _____________________________________________________________________________
#
# main and command line options
#
# _____________________________________________________________________________
def main(argv=sys.argv[1:]):
    # [---CUSTO---]
    # Preprocessing, for example to ensure backward compatibility
    # [---CUSTO---]

    parser = configargparse.ArgumentParser(description='enrollment version ' + enrollment.__version__,
                                           default_config_files=['~/.enrollment.ini'],
                                           formatter_class=configargparse.ArgumentDefaultsRawHelpFormatter)
    parser.add_argument('--config', is_config_file=True, help='config file path')
    parser.add_argument("--do-not-start", default=False, action='store_true', dest='do_not_start',
                        help="Sanity check of the configuration - NOT FOR PRODUCTION")
    parser.add_argument("-i", "--ip", default='0.0.0.0', dest='ip', env_var='ENROLLMENT_IP', help="Listen IP")
    parser.add_argument("-p", "--port", default=8080, dest='port', type=int, env_var='ENROLLMENT_PORT', help="Port number")
    parser.add_argument(      "--monitoring-port", default=0, dest='monitoring_port', type=int, env_var='ENROLLMENT_MONITORING_PORT', help="Port number used for monitoring services. Default is to used the same port as for business services. When defined, monitoring services are exposed through HTTP.")
    parser.add_argument("-l", "--loglevel", default='INFO', dest='loglevel', env_var='ENROLLMENT_LOGLEVEL', help="Log level")
    parser.add_argument("-f", "--logfile", default=None, dest='logfile', env_var='ENROLLMENT_LOGFILE', help="Log file")

    parser.add_argument("-M", "--max-size", type=int, dest='input_max_size', env_var='ENROLLMENT_INPUT_MAX_SIZE',
                        default=10,
                        help="The buffer maximum size accepted (in MB)")
    parser.add_argument("--conf-directory", dest='conf_directory',
                        env_var='ENROLLMENT_CONFIG_DIR',
                        default=['./conf'],
                        action='append',
                        help='Additional directory where configuration will be looked up. Last directory added will be searched first.')

    # arguments used for certificates
    parser.add_argument("--server-certfile", dest='server_certfile', env_var='ENROLLMENT_SERVER_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificate identifying\nthis server')
    parser.add_argument("--server-keyfile", dest='server_keyfile', env_var='ENROLLMENT_SERVER_KEYFILE',
                        default=None,
                        help='The private key identifying this server.')
    parser.add_argument("--server-keyfile-password", dest='server_keyfile_password',
                        env_var='ENROLLMENT_SERVER_KEYFILE_PASSWORD',
                        default=None,
                        help='The password to access the private key')
    parser.add_argument("--server-ca-certfile", dest='server_ca_certfile',
                        env_var='ENROLLMENT_SERVER_CA_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificates of the clients for mutual authent')

    # Add arguments for clients
      
    # arguments to connect to the notification service
    parser.add_argument("--notification-url", dest='notification_url',
                        env_var='ENROLLMENT_NOTIFICATION_URL',
                        default='http://localhost:8080',
                        help='The path to the notification service')
    parser.add_argument("--notification-certfile", dest='notification_certfile',
                        env_var='ENROLLMENT_NOTIFICATION_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificate identifying this client when connecting to the notification service')
    parser.add_argument("--notification-keyfile", dest='notification_keyfile',
                        env_var='ENROLLMENT_NOTIFICATION_KEYFILE',
                        default=None, 
                        help='The private key identifying this client when connecting to the notification service.')
    parser.add_argument("--notification-keyfile-password", dest='notification_keyfile_password',
                        env_var='ENROLLMENT_NOTIFICATION_KEYFILE_PASSWORD',
                        default=None,
                        help='The password to access the private key to used to authenticate when connecting to the notification service.')
    parser.add_argument("--notification-ca-certfile", dest='notification_ca_certfile', 
                        env_var='ENROLLMENT_NOTIFICATION_CA_CERTFILE',
                        default=None, 
                        help='The PEM formatted file containing the certificates authority to validate the server of the notification service')
    

    
    parser.add_argument(      "--custo-filename", default="custo.yaml", dest='custo_filename', env_var='ENROLLMENT_CUSTO_FILENAME', help="File containing the description of the custo (YAML)")
    parser.add_argument(      "--api-file", default=os.path.join(os.path.dirname(__file__), 'enrollment.yaml'), dest='api_file', env_var='ENROLLMENT_API_FILE', help="OpenAPI file for this server (YAML)")
    
    
    parser.add_argument(      "--database-url", default="sqlite:///file:testdb?mode=memory&cache=shared&uri=true", dest='database_url', env_var='ENROLLMENT_DATABASE_URL', help="String to connect to the database")
    parser.add_argument(      "--dont-create-schema", default=False, action='store_true', dest='dont_create_schema', help="Default is to create the schema in the database when connecting. Use this flag to disable this behavior")
    parser.add_argument(      "--dump-schema", default=False, action='store_true', dest='dump_schema', help="Used to dump the DDL of the database schema")
    

    # [---CUSTO---]
    # Additional arguments
    # [---CUSTO---]

    enrollment.args = parser.parse_args(argv)
    enrollment.args.conf_directory.reverse()
    # [---CUSTO---]
    # Extra argument processing
    # [---CUSTO---]

    if enrollment.args.loglevel == 'DEBUG':
        print(parser.format_values())

    # Configure logging
    h = logging.StreamHandler(sys.stdout)
    f = FormatterJSON()
    h.setFormatter(f)
    h.setLevel(logging.getLevelName(enrollment.args.loglevel))
    logging.basicConfig(force=True,
                        level=logging.getLevelName(enrollment.args.loglevel),
                        handlers=[h])
    if enrollment.args.logfile:
        fh = logging.handlers.RotatingFileHandler(enrollment.args.logfile, maxBytes=1000000, backupCount=20)
        fh.setLevel(logging.getLevelName(enrollment.args.loglevel))
        fh.setFormatter(f)
        logging.getLogger().addHandler(fh)

    
    if enrollment.args.dump_schema:
        enrollment.model.dump()
        return
    enrollment.model.setup()
    

    # [---CUSTO---]
    # Extra initialization
    # [---CUSTO---]

    logging.info('Starting')
    enrollment.server.serve()


if __name__ == '__main__':
    main()