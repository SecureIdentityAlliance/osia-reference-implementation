
import sys
import json
import time
import logging
import logging.handlers
import configargparse

import cr
import cr.server

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

    parser = configargparse.ArgumentParser(description='cr version ' + cr.__version__,
                                           default_config_files=['~/.cr.ini'],
                                           formatter_class=configargparse.ArgumentDefaultsRawHelpFormatter)
    parser.add_argument('--config', is_config_file=True, help='config file path')
    parser.add_argument("--do-not-start", default=False, action='store_true', dest='do_not_start',
                        help="Sanity check of the configuration - NOT FOR PRODUCTION")
    parser.add_argument("-i", "--ip", default='0.0.0.0', dest='ip', env_var='CR_IP', help="Listen IP")
    parser.add_argument("-p", "--port", default=8080, dest='port', type=int, env_var='CR_PORT', help="Port number")
    parser.add_argument(      "--monitoring-port", default=0, dest='monitoring_port', type=int, env_var='CR_MONITORING_PORT', help="Port number used for monitoring services. Default is to used the same port as for business services. When defined, monitoring services are exposed through HTTP.")
    parser.add_argument("-l", "--loglevel", default='INFO', dest='loglevel', env_var='CR_LOGLEVEL', help="Log level")
    parser.add_argument("-f", "--logfile", default=None, dest='logfile', env_var='CR_LOGFILE', help="Log file")

    parser.add_argument("-M", "--max-size", type=int, dest='input_max_size', env_var='CR_INPUT_MAX_SIZE',
                        default=10,
                        help="The buffer maximum size accepted (in MB)")
    parser.add_argument("--conf-directory", dest='conf_directory',
                        env_var='CR_CONFIG_DIR',
                        default=['./conf'],
                        action='append',
                        help='Additional directory where configuration will be looked up. Last directory added will be searched first.')

    # arguments used for certificates
    parser.add_argument("--server-certfile", dest='server_certfile', env_var='CR_SERVER_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificate identifying\nthis server')
    parser.add_argument("--server-keyfile", dest='server_keyfile', env_var='CR_SERVER_KEYFILE',
                        default=None,
                        help='The private key identifying this server.')
    parser.add_argument("--server-keyfile-password", dest='server_keyfile_password',
                        env_var='CR_SERVER_KEYFILE_PASSWORD',
                        default=None,
                        help='The password to access the private key')
    parser.add_argument("--server-ca-certfile", dest='server_ca_certfile',
                        env_var='CR_SERVER_CA_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificates of the clients for mutual authent')

    # Add arguments for clients
      
    # arguments to connect to the notification service
    parser.add_argument("--notification-url", dest='notification_url',
                        env_var='CR_NOTIFICATION_URL',
                        default='http://localhost:8080',
                        help='The path to the notification service')
    parser.add_argument("--notification-certfile", dest='notification_certfile',
                        env_var='CR_NOTIFICATION_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificate identifying this client when connecting to the notification service')
    parser.add_argument("--notification-keyfile", dest='notification_keyfile',
                        env_var='CR_NOTIFICATION_KEYFILE',
                        default=None, 
                        help='The private key identifying this client when connecting to the notification service.')
    parser.add_argument("--notification-keyfile-password", dest='notification_keyfile_password',
                        env_var='CR_NOTIFICATION_KEYFILE_PASSWORD',
                        default=None,
                        help='The password to access the private key to used to authenticate when connecting to the notification service.')
    parser.add_argument("--notification-ca-certfile", dest='notification_ca_certfile', 
                        env_var='CR_NOTIFICATION_CA_CERTFILE',
                        default=None, 
                        help='The PEM formatted file containing the certificates authority to validate the server of the notification service')
    
    # arguments to connect to the pr service
    parser.add_argument("--pr-url", dest='pr_url',
                        env_var='CR_PR_URL',
                        default='http://localhost:8080',
                        help='The path to the pr service')
    parser.add_argument("--pr-certfile", dest='pr_certfile',
                        env_var='CR_PR_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificate identifying this client when connecting to the pr service')
    parser.add_argument("--pr-keyfile", dest='pr_keyfile',
                        env_var='CR_PR_KEYFILE',
                        default=None, 
                        help='The private key identifying this client when connecting to the pr service.')
    parser.add_argument("--pr-keyfile-password", dest='pr_keyfile_password',
                        env_var='CR_PR_KEYFILE_PASSWORD',
                        default=None,
                        help='The password to access the private key to used to authenticate when connecting to the pr service.')
    parser.add_argument("--pr-ca-certfile", dest='pr_ca_certfile', 
                        env_var='CR_PR_CA_CERTFILE',
                        default=None, 
                        help='The PEM formatted file containing the certificates authority to validate the server of the pr service')
    
    # arguments to connect to the uin service
    parser.add_argument("--uin-url", dest='uin_url',
                        env_var='CR_UIN_URL',
                        default='http://localhost:8080',
                        help='The path to the uin service')
    parser.add_argument("--uin-certfile", dest='uin_certfile',
                        env_var='CR_UIN_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificate identifying this client when connecting to the uin service')
    parser.add_argument("--uin-keyfile", dest='uin_keyfile',
                        env_var='CR_UIN_KEYFILE',
                        default=None, 
                        help='The private key identifying this client when connecting to the uin service.')
    parser.add_argument("--uin-keyfile-password", dest='uin_keyfile_password',
                        env_var='CR_UIN_KEYFILE_PASSWORD',
                        default=None,
                        help='The password to access the private key to used to authenticate when connecting to the uin service.')
    parser.add_argument("--uin-ca-certfile", dest='uin_ca_certfile', 
                        env_var='CR_UIN_CA_CERTFILE',
                        default=None, 
                        help='The PEM formatted file containing the certificates authority to validate the server of the uin service')
    
    # arguments to connect to the enrollment service
    parser.add_argument("--enrollment-url", dest='enrollment_url',
                        env_var='CR_ENROLLMENT_URL',
                        default='http://localhost:8080',
                        help='The path to the enrollment service')
    parser.add_argument("--enrollment-certfile", dest='enrollment_certfile',
                        env_var='CR_ENROLLMENT_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificate identifying this client when connecting to the enrollment service')
    parser.add_argument("--enrollment-keyfile", dest='enrollment_keyfile',
                        env_var='CR_ENROLLMENT_KEYFILE',
                        default=None, 
                        help='The private key identifying this client when connecting to the enrollment service.')
    parser.add_argument("--enrollment-keyfile-password", dest='enrollment_keyfile_password',
                        env_var='CR_ENROLLMENT_KEYFILE_PASSWORD',
                        default=None,
                        help='The password to access the private key to used to authenticate when connecting to the enrollment service.')
    parser.add_argument("--enrollment-ca-certfile", dest='enrollment_ca_certfile', 
                        env_var='CR_ENROLLMENT_CA_CERTFILE',
                        default=None, 
                        help='The PEM formatted file containing the certificates authority to validate the server of the enrollment service')
    

    
    

    # [---CUSTO---]
    # Additional arguments

    parser.add_argument("--my-url", dest='my_url',
                        env_var='MY_URL',
                        default='http://cr:8080/',
                        help='The URL to reach me')

    # [---CUSTO---]

    cr.args = parser.parse_args(argv)
    cr.args.conf_directory.reverse()
    # [---CUSTO---]
    # Extra argument processing
    # [---CUSTO---]

    if cr.args.loglevel == 'DEBUG':
        print(parser.format_values())

    # Configure logging
    h = logging.StreamHandler(sys.stdout)
    f = FormatterJSON()
    h.setFormatter(f)
    h.setLevel(logging.getLevelName(cr.args.loglevel))
    logging.basicConfig(force=True,
                        level=logging.getLevelName(cr.args.loglevel),
                        handlers=[h])
    if cr.args.logfile:
        fh = logging.handlers.RotatingFileHandler(cr.args.logfile, maxBytes=1000000, backupCount=20)
        fh.setLevel(logging.getLevelName(cr.args.loglevel))
        fh.setFormatter(f)
        logging.getLogger().addHandler(fh)

    

    # [---CUSTO---]
    # Extra initialization
    # [---CUSTO---]

    logging.info('Starting')
    cr.server.serve()


if __name__ == '__main__':
    main()