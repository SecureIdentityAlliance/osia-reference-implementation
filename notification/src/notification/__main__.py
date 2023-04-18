
import sys
import logging
import logging.handlers
import configargparse

import notification
import notification.notification

# _____________________________________________________________________________
#
# main and command line options
#
# _____________________________________________________________________________
def main(argv=sys.argv[1:]):

    parser = configargparse.ArgumentParser(description='notification version ' + notification.__version__,
                                           default_config_files=['~/.notification.ini'],
                                           formatter_class=configargparse.ArgumentDefaultsRawHelpFormatter)
    parser.add_argument('--config', is_config_file=True, help='config file path')
    parser.add_argument("--do-not-start", default=False, action='store_true', dest='do_not_start',
                        help="Sanity check of the configuration - NOT FOR PRODUCTION")
    parser.add_argument("-i", "--ip", default='0.0.0.0', dest='ip', env_var='NOTIFICATION_IP', help="Listen IP")
    parser.add_argument("-p", "--port", default=8080, dest='port', type=int, env_var='NOTIFICATION_PORT', help="Port number")
    parser.add_argument(      "--monitoring-port", default=0, dest='monitoring_port', type=int, env_var='NOTIFICATION_MONITORING_PORT', help="Port number used for monitoring services. Default is to used the same port as for business services. When defined, monitoring services are exposed through HTTP.")
    parser.add_argument("-l", "--loglevel", default='INFO', dest='loglevel', env_var='NOTIFICATION_LOGLEVEL', help="Log level")
    parser.add_argument("-f", "--logfile", default=None, dest='logfile', env_var='NOTIFICATION_LOGFILE', help="Log file")

    parser.add_argument("-M", "--max-size", type=int, dest='input_max_size', env_var='INPUT_MAX_SIZE',
                        default=10,
                        help="The buffer maximum size accepted (in MB)")
    parser.add_argument("--conf-directory", dest='conf_directory',
                        env_var='NOTIFICATION_CONFIG_DIR',
                        default=['./conf'],
                        action='append',
                        help='Additional directory where configuration will be looked up. Last directory added will be searched first.')

    # arguments used for certificates
    parser.add_argument("--server-certfile", dest='server_certfile', env_var='NOTIFICATION_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificate identifying\nthis server')
    parser.add_argument("--server-keyfile", dest='server_keyfile', env_var='NOTIFICATION_KEYFILE',
                        default=None,
                        help='The private key identifying this server.')
    parser.add_argument("--server-keyfile-password", dest='server_keyfile_password',
                        env_var='NOTIFICATION_KEYFILE_PASSWORD',
                        default=None,
                        help='The password to access the private key')
    parser.add_argument("--server-ca-certfile", dest='server_ca_certfile',
                        env_var='NOTIFICATION_CA_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificates of the clients for mutual authent')

    parser.add_argument("--redis-url", dest='redis_url',
                        env_var='REDIS_URL',
                        default='redis://localhost:6379/0',
                        help='The URL to the redis service')
    parser.add_argument("--root-url", dest='root_url',
                        env_var='ROOT_URL',
                        default='http://localhost:8080',
                        help='The URL used to reach this service')

    notification.args = parser.parse_args(argv)
    notification.args.conf_directory.reverse()

    if notification.args.loglevel == 'DEBUG':
        print(parser.format_values())

    logging.basicConfig(format='%(asctime)-15s %(levelname)s - %(message)s',    # NOSONAR
                        level=logging.getLevelName(notification.args.loglevel))
    logging.getLogger('notification').setLevel(logging.getLevelName(notification.args.loglevel))
    if notification.args.logfile:
        fh = logging.handlers.RotatingFileHandler(notification.args.logfile, maxBytes=1000000, backupCount=20)
        fh.setLevel(logging.getLevelName(notification.args.loglevel))
        formatter = logging.Formatter('%(asctime)-15s %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logging.getLogger().addHandler(fh)

    logging.info('Starting')
    notification.notification.serve()


if __name__ == '__main__':
    main()
