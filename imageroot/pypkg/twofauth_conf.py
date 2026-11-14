#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""Shared settings model of the 2FAuth module.

Actions, update hooks and restore steps import this file with:

    sys.path.insert(0, os.path.join(os.environ["AGENT_INSTALL_DIR"], "pypkg"))
    import twofauth_conf

Where each value lives:

- Non-secret settings: the module environment (state/environment), one
  TWOFAUTH_<2FAuth variable> entry each. The restore and clone procedures
  get them back with the environment.
- Secrets (OAuth client secrets, outgoing proxy URL): state/passwords.env,
  mode 0600, never in the environment and never returned by
  get-configuration.
- 2FAuth admin settings stored in the 2FAuth database (SSO only,
  registration...): applied with "php" inside the running container. The
  last value applied by the module is kept in TWOFAUTH_SETTING_* entries.
- state/app.env: generated from the environment for the container,
  never edited by hand.
"""

import json
import os
import subprocess
import sys
import time

ENV_PREFIX = "TWOFAUTH_"
SETTING_PREFIX = "TWOFAUTH_SETTING_"
USERPREF_PREFIX = "TWOFAUTH_USERPREF_"

APP_ENV_FILE = "app.env"
SECRETS_FILE = "passwords.env"
APP_CONTAINER = "2fauth-app"

# Non-secret settings written to app.env.
# json field: (2FAuth variable, type, default, shown on the Settings page)
# Types: str, bool, int, int_or_null
FIELDS = {
    "app_name": ("APP_NAME", "str", "2FAuth", True),
    "mail_from_address": ("MAIL_FROM_ADDRESS", "str", "", True),
    "mail_from_name": ("MAIL_FROM_NAME", "str", "", False),
    "openid_authorize_url": ("OPENID_AUTHORIZE_URL", "str", "", True),
    "openid_token_url": ("OPENID_TOKEN_URL", "str", "", True),
    "openid_userinfo_url": ("OPENID_USERINFO_URL", "str", "", True),
    "openid_client_id": ("OPENID_CLIENT_ID", "str", "", True),
    "openid_http_verify_ssl_peer": ("OPENID_HTTP_VERIFY_SSL_PEER", "bool", True, True),
    "github_client_id": ("GITHUB_CLIENT_ID", "str", "", True),
    "app_timezone": ("APP_TIMEZONE", "str", "UTC", False),
    "log_channel": ("LOG_CHANNEL", "str", "daily", False),
    "log_level": ("LOG_LEVEL", "str", "notice", False),
    "session_lifetime": ("SESSION_LIFETIME", "int", 120, False),
    "login_throttle": ("LOGIN_THROTTLE", "int", 5, False),
    "throttle_api": ("THROTTLE_API", "int_or_null", 60, False),
    "throttle_api_during_import": ("THROTTLE_API_DURING_IMPORT", "int_or_null", 1000, False),
    "authentication_log_retention": ("AUTHENTICATION_LOG_RETENTION", "int", 365, False),
    "otp_log_retention": ("OTP_LOG_RETENTION", "int", 365, False),
    "webauthn_name": ("WEBAUTHN_NAME", "str", "", False),
    "webauthn_user_verification": ("WEBAUTHN_USER_VERIFICATION", "str", "preferred", False),
    "content_security_policy": ("CONTENT_SECURITY_POLICY", "bool", True, False),
    "block_otpauth_imagelink_fetching": ("BLOCK_OPTAUTH_IMAGELINK_FETCHING", "bool", True, False),
    "php_memory_limit_temp_override": ("PHP_MEMORY_LIMIT_TEMP_OVERRIDE", "int", 512, False),
}

# Secrets written to state/passwords.env.
# json field: (2FAuth variable, client id field that owns it, or None)
SECRETS = {
    "openid_client_secret": ("OPENID_CLIENT_SECRET", "openid_client_id"),
    "github_client_secret": ("GITHUB_CLIENT_SECRET", "github_client_id"),
    "proxy_for_outgoing_requests": ("PROXY_FOR_OUTGOING_REQUESTS", None),
}

# 2FAuth admin settings stored in its database.
# json field: (2FAuth setting name, upstream default, shown on the Settings page)
APP_SETTINGS = {
    "enable_sso": ("enableSso", True, True),
    "use_sso_only": ("useSsoOnly", False, True),
    "disable_registration": ("disableRegistration", False, True),
    "keep_sso_registration_enabled": ("keepSsoRegistrationEnabled", False, True),
    "allow_pat_while_sso_only": ("allowPatWhileSsoOnly", False, False),
}

# Values the module always manages: never asked to the admin.
MANAGED = {
    "APP_ENV": "local",
    "APP_DEBUG": "false",
    # The container port is published on 127.0.0.1 only: every request
    # comes from the local Traefik, whatever address the rootless network
    # gives it inside the pod.
    "TRUSTED_PROXIES": "*",
    "AUTHENTICATION_GUARD": "web-guard",
    "CACHE_DRIVER": "file",
    "SESSION_DRIVER": "file",
    "BROADCAST_DRIVER": "log",
    "QUEUE_DRIVER": "sync",
}


def env_name(field):
    return ENV_PREFIX + FIELDS[field][0]


def setting_env_name(field):
    return SETTING_PREFIX + field.upper()


def to_env(ftype, value):
    """Convert a JSON value to its environment string."""
    if ftype == "bool":
        return "true" if value else "false"
    if ftype == "int_or_null" and value is None:
        return "null"
    return str(value)


def from_env(ftype, raw, default):
    """Convert an environment string to its JSON value."""
    if raw is None:
        return default
    if ftype == "bool":
        return raw.strip().lower() in ("true", "1", "yes", "on")
    if ftype in ("int", "int_or_null"):
        if ftype == "int_or_null" and raw.strip().lower() in ("null", ""):
            return None
        try:
            return int(raw)
        except ValueError:
            return default
    return raw


def read_fields(environ):
    """Return every non-secret field from an environment mapping."""
    values = {}
    for field, (_var, ftype, default, _ui) in FIELDS.items():
        values[field] = from_env(ftype, environ.get(env_name(field)), default)
    return values


def read_saved_app_settings(environ):
    """Return the admin settings as last applied by the module, or the
    upstream defaults."""
    values = {}
    for field, (_name, default, _ui) in APP_SETTINGS.items():
        values[field] = from_env("bool", environ.get(setting_env_name(field)), default)
    return values


def read_user_preferences(environ):
    """Return {"THEME": {"default": "light", "locked": true}, ...}"""
    prefs = {}
    for key, raw in environ.items():
        for kind in ("DEFAULT", "LOCKED"):
            prefix = USERPREF_PREFIX + kind + "__"
            if key.startswith(prefix):
                name = key[len(prefix):]
                entry = prefs.setdefault(name, {})
                if kind == "LOCKED":
                    entry["locked"] = from_env("bool", raw, False)
                else:
                    entry["default"] = raw
    return prefs


def user_preferences_env(prefs):
    """Return the TWOFAUTH_USERPREF_* entries of a preferences object."""
    entries = {}
    for name, entry in prefs.items():
        if "default" in entry:
            value = entry["default"]
            if isinstance(value, bool):
                value = "true" if value else "false"
            entries[USERPREF_PREFIX + "DEFAULT__" + name] = str(value)
        if entry.get("locked"):
            entries[USERPREF_PREFIX + "LOCKED__" + name] = "true"
    return entries


def read_secrets(state_dir="."):
    path = os.path.join(state_dir, SECRETS_FILE)
    secrets = {}
    try:
        with open(path) as fp:
            for line in fp:
                line = line.rstrip("\n")
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                secrets[key] = value
    except FileNotFoundError:
        pass
    return secrets


def write_private_envfile(path, envmap):
    """Atomically write an env file readable by the module user only."""
    tmp = path + ".tmp." + str(os.getpid())
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fp:
        for key in sorted(envmap):
            fp.write(key + "=" + str(envmap[key]) + "\n")
        fp.flush()
        os.fsync(fp.fileno())
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def write_secrets(secrets, state_dir="."):
    clean = {k: v for k, v in secrets.items() if v != ""}
    write_private_envfile(os.path.join(state_dir, SECRETS_FILE), clean)


def write_app_env(environ, state_dir="."):
    """Generate state/app.env from the module environment mapping."""
    host = environ.get("TRAEFIK_HOST", "")
    values = read_fields(environ)
    app = dict(MANAGED)
    app["APP_URL"] = "https://" + host if host else "http://localhost"
    for field, (var, ftype, _default, _ui) in FIELDS.items():
        if field in ("mail_from_address", "mail_from_name"):
            continue  # written by bin/discover-smarthost with the mail transport
        value = values[field]
        if field == "webauthn_name" and not value:
            value = values["app_name"]
        if ftype == "str" and value == "":
            continue  # keep the 2FAuth default
        app[var] = to_env(ftype, value)
    for key, value in environ.items():
        if key.startswith(USERPREF_PREFIX):
            app[key[len(ENV_PREFIX):]] = value
    write_private_envfile(os.path.join(state_dir, APP_ENV_FILE), app)


#
# Admin settings stored in the 2FAuth database
#

_PHP = r"""
require '/srv/vendor/autoload.php';
$app = require '/srv/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
$svc = $app->make(App\Services\SettingService::class);
$in = json_decode($argv[1], true);
foreach ($in['set'] as $k => $v) { $svc->set($k, (bool) $v); }
$out = [];
foreach ($in['get'] as $k) { $out[$k] = (bool) $svc->get($k); }
echo "\n@@NS8-JSON@@" . json_encode($out) . "\n";
"""


def container_running():
    proc = subprocess.run(
        ["podman", "container", "inspect", "--format", "{{.State.Running}}", APP_CONTAINER],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
    )
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _php_exchange(set_values, timeout):
    """Run the PHP snippet once; return {setting name: bool} or None."""
    names = [name for (name, _default, _ui) in APP_SETTINGS.values()]
    payload = json.dumps({"set": set_values, "get": names})
    try:
        proc = subprocess.run(
            ["podman", "exec", "-w", "/srv", APP_CONTAINER,
             "php", "-d", "display_errors=stderr", "-r", _PHP, "--", payload],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None
    if proc.returncode != 0:
        print(proc.stderr.strip()[-2000:], file=sys.stderr)
        return None
    for line in reversed(proc.stdout.splitlines()):
        if line.startswith("@@NS8-JSON@@"):
            return json.loads(line[len("@@NS8-JSON@@"):])
    return None


def get_live_app_settings(timeout=30):
    """Read the admin settings from the running 2FAuth; None if it is not
    running or not ready."""
    if not container_running():
        return None
    raw = _php_exchange({}, timeout)
    if raw is None:
        return None
    return {field: raw.get(name, default) for field, (name, default, _ui) in APP_SETTINGS.items()}


def apply_app_settings(changes, wait=300):
    """Write {json field: bool} to the 2FAuth database, waiting until the
    container has finished its startup (database migrations). Return the
    values read back, or None on timeout."""
    set_values = {APP_SETTINGS[field][0]: bool(value) for field, value in changes.items()}
    deadline = time.monotonic() + wait
    while True:
        raw = _php_exchange(set_values, 60)
        if raw is not None:
            return {field: raw.get(name, default) for field, (name, default, _ui) in APP_SETTINGS.items()}
        if time.monotonic() > deadline:
            return None
        time.sleep(5)


#
# Legacy app.env import (module releases up to 2FAuth 8.0.3)
#

def is_legacy_app_env(appenv):
    # Only the old generator wrote the Laravel Mix and Pusher placeholders
    return "MIX_ENV" in appenv or "PUSHER_APP_CLUSTER" in appenv


def legacy_env_entries(appenv, environ):
    """Return the TWOFAUTH_* entries to import from an old app.env. Only
    values that differ from the defaults and are not set yet."""
    imports = {}
    mapping = {
        "LOG_CHANNEL": ("log_channel", ("daily", "stderr", "errorlog", "single")),
        "LOG_LEVEL": ("log_level", ("debug", "info", "notice", "warning", "error", "critical", "alert", "emergency")),
        "SESSION_LIFETIME": ("session_lifetime", None),
        "WEBAUTHN_NAME": ("webauthn_name", None),
    }
    for var, (field, allowed) in mapping.items():
        raw = appenv.get(var)
        if raw is None or env_name(field) in environ:
            continue
        _var, ftype, default, _ui = FIELDS[field]
        if allowed is not None and raw not in allowed:
            continue
        if ftype == "int":
            try:
                if int(raw) < 1:
                    continue
            except ValueError:
                continue
        if field == "webauthn_name" and raw in ("2FAuth", ""):
            continue
        if str(raw) == str(default):
            continue
        imports[env_name(field)] = str(raw)
    return imports
