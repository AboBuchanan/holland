"""Load a holland.conf config file"""
import os
import logging
from holland.core import Config, Configspec, ConfigError
from holland.core import load_plugin

LOG = logging.getLogger(__name__)

cli_configspec = Configspec.parse("""
[holland]
backup-directory = string(default='.')
backupsets       = force_list(default=list())
umask            = integer(default='0007', base=8)
path             = string(default=None)
tmpdir           = string(default=None)

[logging]
file             = string(default='/var/log/holland/holland.log')
format           = string(default='[%(levelname)s] %(message)s')
level            = log_level(default="info")
""".splitlines())

class GlobalHollandConfig(Config):
    name = None

    def basedir(self):
        return os.path.abspath(os.path.dirname(self.name or '.'))

    def load_backupset(self, name):
        if not os.path.isabs(name):
            name = os.path.join(self.basedir(), 'backupsets', name)
        if not os.path.isdir(name) and not name.endswith('.conf'):
            name += '.conf'

        LOG.info("Loading %s", name)

        cfg = Config.read([name])

        # load providers/$plugin.conf if available
        plugin = cfg.get('holland:backup', {}).get('plugin')
        if plugin:
            provider_path = os.path.join(self.basedir(),
                                         'providers',
                                         plugin + '.conf')
            try:
                cfg.meld(Config.read([provider_path]))
            except ConfigError:
                LOG.debug("No global provider found.  Skipping.")
        cfg.name = os.path.splitext(os.path.basename(name))[0]
        return cfg

    #@classmethod
    def configspec(self):
        return cli_configspec
    configspec = classmethod(configspec)

def load_global_config(path):
    if path:
        cfg = GlobalHollandConfig.read([path])
        cfg.name = path
    else:
        cfg = GlobalHollandConfig()

    cfg.configspec().validate(cfg)
    return cfg