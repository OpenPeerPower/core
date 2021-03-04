"""Consts for Cast integration."""

DOMAIN = "cast"
DEFAULT_PORT = 8009

# Stores a threading.Lock that is held by the internal pychromecast discovery.
INTERNAL_DISCOVERY_RUNNING_KEY = "cast_discovery_running"
# Stores all ChromecastInfo we encountered through discovery or config as a set
# If we find a chromecast with a new host, the old one will be removed again.
KNOWN_CHROMECAST_INFO_KEY = "cast_known_chromecasts"
# Stores UUIDs of cast devices that were added as entities. Doesn't store
# None UUIDs.
ADDED_CAST_DEVICES_KEY = "cast_added_cast_devices"
# Stores an audio group manager.
CAST_MULTIZONE_MANAGER_KEY = "cast_multizone_manager"
# Store a CastBrowser
CAST_BROWSER_KEY = "cast_browser"

# Dispatcher signal fired with a ChromecastInfo every time we discover a new
# Chromecast or receive it through configuration
SIGNAL_CAST_DISCOVERED = "cast_discovered"

# Dispatcher signal fired with a ChromecastInfo every time a Chromecast is
# removed
SIGNAL_CAST_REMOVED = "cast_removed"

# Dispatcher signal fired when a Chromecast should show a Open Peer Power Cast view.
SIGNAL_OPP_CAST_SHOW_VIEW = "cast_show_view"

CONF_KNOWN_HOSTS = "known_hosts"
