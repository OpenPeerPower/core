"""Time-based One Time Password auth module."""
import asyncio
from io import BytesIO
from typing import Any, Dict, Optional, Tuple

import voluptuous as vol

from openpeerpower.auth.models import User
from openpeerpower.core import OpenPeerPower

from . import (
    MULTI_FACTOR_AUTH_MODULE_SCHEMA,
    MULTI_FACTOR_AUTH_MODULES,
    MultiFactorAuthModule,
    SetupFlow,
)

REQUIREMENTS = ["pyotp==2.3.0", "PyQRCode==1.2.1"]

CONFIG_SCHEMA = MULTI_FACTOR_AUTH_MODULE_SCHEMA.extend({}, extra=vol.PREVENT_EXTRA)

STORAGE_VERSION = 1
STORAGE_KEY = "auth_module.totp"
STORAGE_USERS = "users"
STORAGE_USER_ID = "user_id"
STORAGE_OTA_SECRET = "ota_secret"

INPUT_FIELD_CODE = "code"

DUMMY_SECRET = "FPPTH34D4E3MI2HG"


def _generate_qr_code(data: str) -> str:
    """Generate a base64 PNG string represent QR Code image of data."""
    import pyqrcode  # pylint: disable=import-outside-toplevel

    qr_code = pyqrcode.create(data)

    with BytesIO() as buffer:
        qr_code.svg(file=buffer, scale=4)
        return str(
            buffer.getvalue()
            .decode("ascii")
            .replace("\n", "")
            .replace(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<svg xmlns="http://www.w3.org/2000/svg"',
                "<svg",
            )
        )


def _generate_secret_and_qr_code(username: str) -> Tuple[str, str, str]:
    """Generate a secret, url, and QR code."""
    import pyotp  # pylint: disable=import-outside-toplevel

    ota_secret = pyotp.random_base32()
    url = pyotp.totp.TOTP(ota_secret).provisioning_uri(
        username, issuer_name="Open Peer Power"
    )
    image = _generate_qr_code(url)
    return ota_secret, url, image


@MULTI_FACTOR_AUTH_MODULES.register("totp")
class TotpAuthModule(MultiFactorAuthModule):
    """Auth module validate time-based one time password."""

    DEFAULT_TITLE = "Time-based One Time Password"
    MAX_RETRY_TIME = 5

    def __init__(self,.opp: OpenPeerPower, config: Dict[str, Any]) -> None:
        """Initialize the user data store."""
        super().__init__.opp, config)
        self._users: Optional[Dict[str, str]] = None
        self._user_store = opp.helpers.storage.Store(
            STORAGE_VERSION, STORAGE_KEY, private=True
        )
        self._init_lock = asyncio.Lock()

    @property
    def input_schema(self) -> vol.Schema:
        """Validate login flow input data."""
        return vol.Schema({INPUT_FIELD_CODE: str})

    async def _async_load(self) -> None:
        """Load stored data."""
        async with self._init_lock:
            if self._users is not None:
                return

            data = await self._user_store.async_load()

            if data is None:
                data = {STORAGE_USERS: {}}

            self._users = data.get(STORAGE_USERS, {})

    async def _async_save(self) -> None:
        """Save data."""
        await self._user_store.async_save({STORAGE_USERS: self._users})

    def _add_ota_secret(self, user_id: str, secret: Optional[str] = None) -> str:
        """Create a ota_secret for user."""
        import pyotp  # pylint: disable=import-outside-toplevel

        ota_secret: str = secret or pyotp.random_base32()

        self._users[user_id] = ota_secret  # type: ignore
        return ota_secret

    async def async_setup_flow(self, user_id: str) -> SetupFlow:
        """Return a data entry flow handler for setup module.

        Mfa module should extend SetupFlow
        """
        user = await self.opp.auth.async_get_user(user_id)
        assert user is not None
        return TotpSetupFlow(self, self.input_schema, user)

    async def async_setup_user(self, user_id: str, setup_data: Any) -> str:
        """Set up auth module for user."""
        if self._users is None:
            await self._async_load()

        result = await self.opp.async_add_executor_job(
            self._add_ota_secret, user_id, setup_data.get("secret")
        )

        await self._async_save()
        return result

    async def async_depose_user(self, user_id: str) -> None:
        """Depose auth module for user."""
        if self._users is None:
            await self._async_load()

        if self._users.pop(user_id, None):  # type: ignore
            await self._async_save()

    async def async_is_user_setup(self, user_id: str) -> bool:
        """Return whether user is setup."""
        if self._users is None:
            await self._async_load()

        return user_id in self._users  # type: ignore

    async def async_validate(self, user_id: str, user_input: Dict[str, Any]) -> bool:
        """Return True if validation passed."""
        if self._users is None:
            await self._async_load()

        # user_input has been validate in caller
        # set INPUT_FIELD_CODE as vol.Required is not user friendly
        return await self.opp.async_add_executor_job(
            self._validate_2fa, user_id, user_input.get(INPUT_FIELD_CODE, "")
        )

    def _validate_2fa(self, user_id: str, code: str) -> bool:
        """Validate two factor authentication code."""
        import pyotp  # pylint: disable=import-outside-toplevel

        ota_secret = self._users.get(user_id)  # type: ignore
        if ota_secret is None:
            # even we cannot find user, we still do verify
            # to make timing the same as if user was found.
            pyotp.TOTP(DUMMY_SECRET).verify(code, valid_window=1)
            return False

        return bool(pyotp.TOTP(ota_secret).verify(code, valid_window=1))


class TotpSetupFlow(SetupFlow):
    """Handler for the setup flow."""

    def __init__(
        self, auth_module: TotpAuthModule, setup_schema: vol.Schema, user: User
    ) -> None:
        """Initialize the setup flow."""
        super().__init__(auth_module, setup_schema, user.id)
        # to fix typing complaint
        self._auth_module: TotpAuthModule = auth_module
        self._user = user
        self._ota_secret: Optional[str] = None
        self._url = None  # type Optional[str]
        self._image = None  # type Optional[str]

    async def async_step_init(
        self, user_input: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Handle the first step of setup flow.

        Return self.async_show_form(step_id='init') if user_input is None.
        Return self.async_create_entry(data={'result': result}) if finish.
        """
        import pyotp  # pylint: disable=import-outside-toplevel

        errors: Dict[str, str] = {}

        if user_input:
            verified = await self.opp.async_add_executor_job(
                pyotp.TOTP(self._ota_secret).verify, user_input["code"]
            )
            if verified:
                result = await self._auth_module.async_setup_user(
                    self._user_id, {"secret": self._ota_secret}
                )
                return self.async_create_entry(
                    title=self._auth_module.name, data={"result": result}
                )

            errors["base"] = "invalid_code"

        else:
            opp = self._auth_module.opp
            (
                self._ota_secret,
                self._url,
                self._image,
            ) = await opp.async_add_executor_job(
                _generate_secret_and_qr_code,  # type: ignore
                str(self._user.name),
            )

        return self.async_show_form(
            step_id="init",
            data_schema=self._setup_schema,
            description_placeholders={
                "code": self._ota_secret,
                "url": self._url,
                "qr_code": self._image,
            },
            errors=errors,
        )
