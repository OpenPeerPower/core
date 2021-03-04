"""Support for Proxmox VE."""
from datetime import timedelta
import logging

from proxmoxer import ProxmoxAPI
from proxmoxer.backends.https import AuthenticationError
from proxmoxer.core import ResourceException
from requests.exceptions import SSLError
import voluptuous as vol

from openpeerpower.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from openpeerpower.core import OpenPeerPower
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

PLATFORMS = ["binary_sensor"]
DOMAIN = "proxmoxve"
PROXMOX_CLIENTS = "proxmox_clients"
CONF_REALM = "realm"
CONF_NODE = "node"
CONF_NODES = "nodes"
CONF_VMS = "vms"
CONF_CONTAINERS = "containers"

COORDINATOR = "coordinator"
API_DATA = "api_data"

DEFAULT_PORT = 8006
DEFAULT_REALM = "pam"
DEFAULT_VERIFY_SSL = True
TYPE_VM = 0
TYPE_CONTAINER = 1
UPDATE_INTERVAL = 60

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Required(CONF_HOST): cv.string,
                        vol.Required(CONF_USERNAME): cv.string,
                        vol.Required(CONF_PASSWORD): cv.string,
                        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                        vol.Optional(CONF_REALM, default=DEFAULT_REALM): cv.string,
                        vol.Optional(
                            CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL
                        ): cv.boolean,
                        vol.Required(CONF_NODES): vol.All(
                            cv.ensure_list,
                            [
                                vol.Schema(
                                    {
                                        vol.Required(CONF_NODE): cv.string,
                                        vol.Optional(CONF_VMS, default=[]): [
                                            cv.positive_int
                                        ],
                                        vol.Optional(CONF_CONTAINERS, default=[]): [
                                            cv.positive_int
                                        ],
                                    }
                                )
                            ],
                        ),
                    }
                )
            ],
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the platform."""
    opp.data.setdefault(DOMAIN, {})

    def build_client() -> ProxmoxAPI:
        """Build the Proxmox client connection."""
        opp.data[PROXMOX_CLIENTS] = {}
        for entry in config[DOMAIN]:
            host = entry[CONF_HOST]
            port = entry[CONF_PORT]
            user = entry[CONF_USERNAME]
            realm = entry[CONF_REALM]
            password = entry[CONF_PASSWORD]
            verify_ssl = entry[CONF_VERIFY_SSL]

            try:
                # Construct an API client with the given data for the given host
                proxmox_client = ProxmoxClient(
                    host, port, user, realm, password, verify_ssl
                )
                proxmox_client.build_client()
            except AuthenticationError:
                _LOGGER.warning(
                    "Invalid credentials for proxmox instance %s:%d", host, port
                )
                continue
            except SSLError:
                _LOGGER.error(
                    'Unable to verify proxmox server SSL. Try using "verify_ssl: false"'
                )
                continue

            return proxmox_client

    proxmox_client = await opp.async_add_executor_job(build_client)

    async def async_update_data() -> dict:
        """Fetch data from API endpoint."""

        proxmox = proxmox_client.get_api_client()

        def poll_api() -> dict:
            data = {}

            for host_config in config[DOMAIN]:
                host_name = host_config["host"]

                data[host_name] = {}

                for node_config in host_config["nodes"]:
                    node_name = node_config["node"]
                    data[host_name][node_name] = {}

                    for vm_id in node_config["vms"]:
                        data[host_name][node_name][vm_id] = {}

                        vm_status = call_api_container_vm(
                            proxmox, node_name, vm_id, TYPE_VM
                        )

                        if vm_status is None:
                            _LOGGER.warning("Vm/Container %s unable to be found", vm_id)
                            data[host_name][node_name][vm_id] = None
                            continue

                        data[host_name][node_name][vm_id] = parse_api_container_vm(
                            vm_status
                        )

                    for container_id in node_config["containers"]:
                        data[host_name][node_name][container_id] = {}

                        container_status = call_api_container_vm(
                            proxmox, node_name, container_id, TYPE_CONTAINER
                        )

                        if container_status is None:
                            _LOGGER.error(
                                "Vm/Container %s unable to be found", container_id
                            )
                            data[host_name][node_name][container_id] = None
                            continue

                        data[host_name][node_name][
                            container_id
                        ] = parse_api_container_vm(container_status)

            return data

        return await opp.async_add_executor_job(poll_api)

    coordinator = DataUpdateCoordinator(
        opp,
        _LOGGER,
        name="proxmox_coordinator",
        update_method=async_update_data,
        update_interval=timedelta(seconds=UPDATE_INTERVAL),
    )

    opp.data[DOMAIN][COORDINATOR] = coordinator

    # Fetch initial data
    await coordinator.async_refresh()

    for platform in PLATFORMS:
        await opp.async_create_task(
            opp.helpers.discovery.async_load_platform(
                platform, DOMAIN, {"config": config}, config
            )
        )

    return True


def parse_api_container_vm(status):
    """Get the container or vm api data and return it formatted in a dictionary.

    It is implemented in this way to allow for more data to be added for sensors
    in the future.
    """

    return {"status": status["status"], "name": status["name"]}


def call_api_container_vm(proxmox, node_name, vm_id, machine_type):
    """Make proper api calls."""
    status = None

    try:
        if machine_type == TYPE_VM:
            status = proxmox.nodes(node_name).qemu(vm_id).status.current.get()
        elif machine_type == TYPE_CONTAINER:
            status = proxmox.nodes(node_name).lxc(vm_id).status.current.get()
    except ResourceException:
        return None

    return status


class ProxmoxEntity(CoordinatorEntity):
    """Represents any entity created for the Proxmox VE platform."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        unique_id,
        name,
        icon,
        host_name,
        node_name,
        vm_id=None,
    ):
        """Initialize the Proxmox entity."""
        super().__init__(coordinator)

        self.coordinator = coordinator
        self._unique_id = unique_id
        self._name = name
        self._host_name = host_name
        self._icon = icon
        self._available = True
        self._node_name = node_name
        self._vm_id = vm_id

        self._state = None

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self) -> str:
        """Return the mdi icon of the entity."""
        return self._icon

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self._available


class ProxmoxClient:
    """A wrapper for the proxmoxer ProxmoxAPI client."""

    def __init__(self, host, port, user, realm, password, verify_ssl):
        """Initialize the ProxmoxClient."""

        self._host = host
        self._port = port
        self._user = user
        self._realm = realm
        self._password = password
        self._verify_ssl = verify_ssl

        self._proxmox = None
        self._connection_start_time = None

    def build_client(self):
        """Construct the ProxmoxAPI client. Allows inserting the realm within the `user` value."""

        if "@" in self._user:
            user_id = self._user
        else:
            user_id = f"{self._user}@{self._realm}"

        self._proxmox = ProxmoxAPI(
            self._host,
            port=self._port,
            user=user_id,
            password=self._password,
            verify_ssl=self._verify_ssl,
        )

    def get_api_client(self):
        """Return the ProxmoxAPI client."""
        return self._proxmox
