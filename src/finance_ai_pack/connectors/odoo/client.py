from __future__ import annotations

import socket
import ssl
from urllib.parse import urlparse
from xmlrpc.client import Fault, ProtocolError, ServerProxy

from finance_ai_pack.config import Settings


class OdooConnectionError(RuntimeError):
    """Raised when live Odoo cannot be reached or authenticated."""


class OdooClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._uid: int | None = None
        self._common: ServerProxy | None = None
        self._models: ServerProxy | None = None

    def is_live_enabled(self) -> bool:
        return (
            not self.settings.fixture_mode
            and bool(self.settings.odoo_url)
            and bool(self.settings.odoo_db)
            and bool(self.settings.odoo_username)
            and bool(self.settings.odoo_password)
        )

    def _validate_required(self) -> None:
        missing = [
            key
            for key, value in {
                "ODOO_URL": self.settings.odoo_url,
                "ODOO_DB": self.settings.odoo_db,
                "ODOO_USERNAME": self.settings.odoo_username,
                "ODOO_PASSWORD": self.settings.odoo_password,
            }.items()
            if not value
        ]
        if missing:
            raise OdooConnectionError(
                f"Missing live Odoo configuration: {', '.join(sorted(missing))}"
            )

    def connect(self) -> None:
        if self._uid is not None and self._models is not None:
            return
        self._validate_required()

        base_url = self.settings.odoo_url.rstrip("/")
        try:
            parsed = urlparse(base_url)
            if not parsed.scheme or not parsed.netloc:
                raise OdooConnectionError(
                    "ODOO_URL must include scheme and host, e.g. https://odoo.example.com"
                )

            common = ServerProxy(f"{base_url}/xmlrpc/2/common", allow_none=True)
            models = ServerProxy(f"{base_url}/xmlrpc/2/object", allow_none=True)
            uid = common.authenticate(
                self.settings.odoo_db,
                self.settings.odoo_username,
                self.settings.odoo_password,
                {},
            )
        except socket.gaierror as exc:
            raise OdooConnectionError(
                f"Unable to resolve Odoo host from ODOO_URL '{base_url}'."
            ) from exc
        except TimeoutError as exc:
            raise OdooConnectionError("Timed out while connecting to Odoo XML-RPC endpoint.") from exc
        except ConnectionRefusedError as exc:
            raise OdooConnectionError("Connection refused by Odoo host/port.") from exc
        except ssl.SSLError as exc:
            raise OdooConnectionError(
                "SSL/TLS handshake failed for ODOO_URL. Check certificate/URL."
            ) from exc
        except ProtocolError as exc:
            raise OdooConnectionError(
                f"Odoo XML-RPC protocol error ({exc.errcode}): {exc.errmsg}"
            ) from exc
        except OdooConnectionError:
            raise
        except Exception as exc:  # pragma: no cover - defensive network error mapping
            raise OdooConnectionError(f"Failed to connect to Odoo: {exc}") from exc

        if not uid:
            raise OdooConnectionError(
                "Odoo authentication failed. Check ODOO_DB, ODOO_USERNAME, and ODOO_PASSWORD."
            )

        self._uid = uid
        self._common = common
        self._models = models

    def search_read(
        self,
        model: str,
        domain: list,
        fields: list[str] | None = None,
        limit: int | None = None,
        offset: int = 0,
        order: str | None = None,
    ) -> list[dict]:
        self.connect()
        kwargs: dict = {"offset": offset}
        if fields is not None:
            kwargs["fields"] = fields
        if limit is not None:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        return self._execute(model, "search_read", [domain], kwargs)

    def read(self, model: str, ids: list[int], fields: list[str] | None = None) -> list[dict]:
        self.connect()
        kwargs = {"fields": fields} if fields is not None else {}
        return self._execute(model, "read", [ids], kwargs)

    def _execute(self, model: str, method: str, args: list, kwargs: dict | None = None) -> list[dict]:
        if self._models is None or self._uid is None:
            raise OdooConnectionError("Odoo client is not connected.")
        try:
            return self._models.execute_kw(
                self.settings.odoo_db,
                self._uid,
                self.settings.odoo_password,
                model,
                method,
                args,
                kwargs or {},
            )
        except Fault as exc:
            message = str(exc)
            if "AccessError" in message:
                raise OdooConnectionError(
                    f"Odoo access denied for model '{model}'. Verify user permissions."
                ) from exc
            if "database" in message.lower() and "not exist" in message.lower():
                raise OdooConnectionError(
                    f"Odoo database '{self.settings.odoo_db}' was not found."
                ) from exc
            raise OdooConnectionError(f"Odoo XML-RPC fault calling {model}.{method}: {message}") from exc
