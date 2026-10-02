
import sys
import os
import json
import time
import logging
import logging.handlers
import configargparse

import cms
import cms.server

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

    parser = configargparse.ArgumentParser(description='cms version ' + cms.__version__,
                                           default_config_files=['~/.cms.ini'],
                                           formatter_class=configargparse.ArgumentDefaultsRawHelpFormatter)
    parser.add_argument('--config', is_config_file=True, help='config file path')
    parser.add_argument("--do-not-start", default=False, action='store_true', dest='do_not_start',
                        help="Sanity check of the configuration - NOT FOR PRODUCTION")
    parser.add_argument("-i", "--ip", default='0.0.0.0', dest='ip', env_var='CMS_IP', help="Listen IP")
    parser.add_argument("-p", "--port", default=8080, dest='port', type=int, env_var='CMS_PORT', help="Port number")
    parser.add_argument(      "--monitoring-port", default=0, dest='monitoring_port', type=int, env_var='CMS_MONITORING_PORT', help="Port number used for monitoring services. Default is to used the same port as for business services. When defined, monitoring services are exposed through HTTP.")
    parser.add_argument("-l", "--loglevel", default='INFO', dest='loglevel', env_var='CMS_LOGLEVEL', help="Log level")
    parser.add_argument("-f", "--logfile", default=None, dest='logfile', env_var='CMS_LOGFILE', help="Log file")

    parser.add_argument("-M", "--max-size", type=int, dest='input_max_size', env_var='CMS_INPUT_MAX_SIZE',
                        default=10,
                        help="The buffer maximum size accepted (in MB)")
    parser.add_argument("--conf-directory", dest='conf_directory',
                        env_var='CMS_CONFIG_DIR',
                        default=['./conf'],
                        action='append',
                        help='Additional directory where configuration will be looked up. Last directory added will be searched first.')

    # arguments used for certificates
    parser.add_argument("--server-certfile", dest='server_certfile', env_var='CMS_SERVER_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificate identifying\nthis server')
    parser.add_argument("--server-keyfile", dest='server_keyfile', env_var='CMS_SERVER_KEYFILE',
                        default=None,
                        help='The private key identifying this server.')
    parser.add_argument("--server-keyfile-password", dest='server_keyfile_password',
                        env_var='CMS_SERVER_KEYFILE_PASSWORD',
                        default=None,
                        help='The password to access the private key')
    parser.add_argument("--server-ca-certfile", dest='server_ca_certfile',
                        env_var='CMS_SERVER_CA_CERTFILE',
                        default=None,
                        help='Path to a PEM formatted file containing the certificates of the clients for mutual authent')

    # Add arguments for clients
      

    
    parser.add_argument(      "--custo-filename", default="custo.yaml", dest='custo_filename', env_var='CMS_CUSTO_FILENAME', help="File containing the description of the custo (YAML)")
    parser.add_argument(      "--api-file", default=os.path.join(os.path.dirname(__file__), 'cms.yaml'), dest='api_file', env_var='CMS_API_FILE', help="OpenAPI file for this server (YAML)")
    
    

    # [---CUSTO---]
    # Additional arguments
    # [---CUSTO---]

    cms.args = parser.parse_args(argv)
    cms.args.conf_directory.reverse()
    # [---CUSTO---]
    # Extra argument processing
    # [---CUSTO---]

    if cms.args.loglevel == 'DEBUG':
        print(parser.format_values())

    # Configure logging
    h = logging.StreamHandler(sys.stdout)
    f = FormatterJSON()
    h.setFormatter(f)
    h.setLevel(logging.getLevelName(cms.args.loglevel))
    logging.basicConfig(force=True,
                        level=logging.getLevelName(cms.args.loglevel),
                        handlers=[h])
    if cms.args.logfile:
        fh = logging.handlers.RotatingFileHandler(cms.args.logfile, maxBytes=1000000, backupCount=20)
        fh.setLevel(logging.getLevelName(cms.args.loglevel))
        fh.setFormatter(f)
        logging.getLogger().addHandler(fh)

    

    # [---CUSTO---]
    # Extra initialization
    # [---CUSTO---]

    logging.info('Starting')
    cms.server.serve()


if __name__ == '__main__':
    main()