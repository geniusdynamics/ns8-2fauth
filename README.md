# ns8-2fauth

NethServer 8 module for [2FAuth](https://docs.2fauth.app/), a web app to
manage Two-Factor Authentication (2FA) accounts and generate their security
codes.

Current 2FAuth version: **9.0.1** (image `docker.io/2fauth/2fauth:9.0.1`).

## Install

Instantiate the module with:

    add-module ghcr.io/geniusdynamics/2fauth:latest 1

The output of the command will return the instance name.
Output example:

    {"module_id": "2fauth1", "image_name": "2fauth", "image_url": "ghcr.io/geniusdynamics/2fauth:latest"}

The first account registered in 2FAuth becomes its administrator: register
it before you disable registration.

## Configure

Let's assume that the instance is named `2fauth1`. The Settings page of the
module runs `configure-module`. From the command line:

```
api-cli run configure-module --agent module/2fauth1 --data - <<EOF
{
  "host": "2fauth.domain.com",
  "http2https": true,
  "lets_encrypt": false
}
EOF
```

`host`, `http2https` and `lets_encrypt` are required. Every other field is
optional: **an absent field keeps its saved value**, so the Settings page
never resets the fields that are configurable from the CLI only. The full
schema, with a description of each field, is in
`imageroot/actions/configure-module/validate-input.json`.

### Settings page fields

| Field | 2FAuth setting | Default | Notes |
|---|---|---|---|
| `host` | `APP_URL` (`https://<host>`) | | Traefik route host name |
| `http2https` | | `true` | Redirect HTTP to HTTPS |
| `lets_encrypt` | | `false` | Request a Let's Encrypt certificate |
| `app_name` | `APP_NAME` | `2FAuth` | Changing it logs every user out |
| `mail_from_address` | `MAIL_FROM_ADDRESS` | empty | Empty: the smarthost user name if it is an e-mail address, else `noreply@<host>` |
| `disable_registration` | admin setting `disableRegistration` | `false` | |
| `enable_sso` | admin setting `enableSso` | `true` | |
| `use_sso_only` | admin setting `useSsoOnly` | `false` | Needs SSO enabled and a configured provider |
| `keep_sso_registration_enabled` | admin setting `keepSsoRegistrationEnabled` | `false` | Create the account at the first SSO login, even with registration disabled |
| `openid_client_id` | `OPENID_CLIENT_ID` | empty | Empty disables OpenID and removes its saved secret |
| `openid_client_secret` | `OPENID_CLIENT_SECRET` | | Write only. Empty keeps the saved secret |
| `openid_authorize_url` | `OPENID_AUTHORIZE_URL` | empty | Required with a client ID |
| `openid_token_url` | `OPENID_TOKEN_URL` | empty | Required with a client ID |
| `openid_userinfo_url` | `OPENID_USERINFO_URL` | empty | Required with a client ID |
| `openid_http_verify_ssl_peer` | `OPENID_HTTP_VERIFY_SSL_PEER` | `true` | Disable only for a self-signed provider |
| `github_client_id` | `GITHUB_CLIENT_ID` | empty | Empty disables GitHub login and removes its saved secret |
| `github_client_secret` | `GITHUB_CLIENT_SECRET` | | Write only. Empty keeps the saved secret |

The admin settings (`disable_registration`, `enable_sso`, `use_sso_only`,
`keep_sso_registration_enabled`, `allow_pat_while_sso_only`) are not
environment variables: 2FAuth stores them in its database, and they are also
editable in the 2FAuth Admin panel. The module writes one only when its value
changes from the last one the module applied, so a change made in the Admin
panel survives a save of unrelated fields. `get-configuration` reads their
live values from the running 2FAuth (`"app_settings_source": "live"`), or
returns the last applied values when 2FAuth is not running (`"saved"`).

### SSO callback URLs

Register these URLs with the providers (the paths are fixed by 2FAuth):

- OpenID Connect redirect URI: `https://<host>/socialite/callback/openid`
- GitHub OAuth app authorization callback URL: `https://<host>/socialite/callback/github`

The Settings page shows them for the configured host. See also the
[2FAuth SSO documentation](https://docs.2fauth.app/security/authentication/sso/).

OpenID example:

```
api-cli run configure-module --agent module/2fauth1 --data - <<EOF
{
  "host": "2fauth.domain.com", "http2https": true, "lets_encrypt": true,
  "enable_sso": true, "keep_sso_registration_enabled": true,
  "openid_authorize_url": "https://idp.domain.com/application/o/authorize/",
  "openid_token_url": "https://idp.domain.com/application/o/token/",
  "openid_userinfo_url": "https://idp.domain.com/application/o/userinfo/",
  "openid_client_id": "2fauth",
  "openid_client_secret": "the-client-secret"
}
EOF
```

### CLI-only fields

| Field | 2FAuth variable | Default |
|---|---|---|
| `mail_from_name` | `MAIL_FROM_NAME` | empty: the application name |
| `app_timezone` | `APP_TIMEZONE` | `UTC` (existing records are not converted) |
| `log_channel` | `LOG_CHANNEL`: `daily`, `single`, `stderr` (journal), `errorlog` | `daily` |
| `log_level` | `LOG_LEVEL` | `notice` |
| `session_lifetime` | `SESSION_LIFETIME` (minutes) | `120` |
| `login_throttle` | `LOGIN_THROTTLE` | `5` |
| `throttle_api` | `THROTTLE_API` (`null` disables) | `60` |
| `throttle_api_during_import` | `THROTTLE_API_DURING_IMPORT` (`null` disables) | `1000` |
| `authentication_log_retention` | `AUTHENTICATION_LOG_RETENTION` (days) | `365` |
| `otp_log_retention` | `OTP_LOG_RETENTION` (days) | `365` |
| `webauthn_name` | `WEBAUTHN_NAME` | empty: the application name |
| `webauthn_user_verification` | `WEBAUTHN_USER_VERIFICATION`: `required`, `preferred`, `discouraged` | `preferred` |
| `content_security_policy` | `CONTENT_SECURITY_POLICY` | `true` |
| `block_otpauth_imagelink_fetching` | `BLOCK_OPTAUTH_IMAGELINK_FETCHING` | `true` |
| `php_memory_limit_temp_override` | `PHP_MEMORY_LIMIT_TEMP_OVERRIDE` (MB) | `512` |
| `allow_pat_while_sso_only` | admin setting `allowPatWhileSsoOnly` | `false` |
| `proxy_for_outgoing_requests` | `PROXY_FOR_OUTGOING_REQUESTS` | write only; absent keeps, `""` removes |
| `user_preferences` | `USERPREF_DEFAULT__<NAME>`, `USERPREF_LOCKED__<NAME>` | `{}` |

`user_preferences` maps upper-case preference names to their default value
and lock, and replaces the saved object (`{}` removes all). See the
[user preferences documentation](https://docs.2fauth.app/getting-started/config/user-preferences/):

```
api-cli run configure-module --agent module/2fauth1 --data - <<EOF
{
  "host": "2fauth.domain.com", "http2https": true, "lets_encrypt": true,
  "app_timezone": "Europe/Rome", "log_channel": "stderr",
  "user_preferences": {"THEME": {"default": "dark", "locked": true}, "LANG": {"default": "it"}}
}
EOF
```

### Managed by the module

These are never asked: `APP_URL` (from `host`), `APP_KEY` (generated at
install), the SQLite database and storage paths (volume `2fauth-app`), the
container port, `TRUSTED_PROXIES` (`*`: the port is published on 127.0.0.1
only, so every request comes from the local Traefik),
`AUTHENTICATION_GUARD=web-guard` (the reverse-proxy guard would trust headers
that any client can send through Traefik), the cache, session and queue
drivers, and the mail transport.

### Where the values live

- `state/environment`: non-secret settings, as `TWOFAUTH_<VARIABLE>`, and
  the last applied admin settings, as `TWOFAUTH_SETTING_<FIELD>`
- `state/passwords.env` (mode 0600): OAuth client secrets and the outgoing
  proxy URL. Never in the environment, never returned by
  `get-configuration`, which returns `openid_client_secret_set`,
  `github_client_secret_set` and `proxy_for_outgoing_requests_set` instead
- `state/key.env` (mode 0600): `APP_KEY`. Never change it: the database
  content is encrypted with it
- `state/app.env`: generated for the container by `configure-module`
- `state/smarthost.env` (mode 0600): mail settings, generated at each start

## Get the configuration

```
api-cli run get-configuration --agent module/2fauth1
```

## Smarthost

Mail goes through the cluster [smarthost](https://nethserver.github.io/ns8-core/core/smarthost/).
Every time 2FAuth starts, `bin/discover-smarthost` writes
`state/smarthost.env` (`MAIL_MAILER`, `MAIL_HOST`, `MAIL_PORT`,
`MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_ENCRYPTION`, `MAIL_VERIFY_SSL_PEER`,
`MAIL_FROM_ADDRESS`, `MAIL_FROM_NAME`). With no smarthost, 2FAuth writes the
messages to its log. The `smarthost-changed` event restarts the container.

## Backup and restore

The backup holds the `2fauth-app` volume (database, Passport keys, logs,
icons), the `2fauth-config` volume, `state/key.env`, `state/passwords.env` and
the module environment. Restore and clone never request a Let's Encrypt
certificate: turn it on again once DNS points to the new node. Backups made by
earlier module releases (2FAuth up to 8.0.3) restore too: `APP_KEY` comes back
from `state/key.env` and the customized values of the old `state/app.env` are
imported.

## Update

```
api-cli run update-module --data '{"module_url":"ghcr.io/geniusdynamics/2fauth:latest","instances":["2fauth1"],"force":true}'
```

### Upgrade notes: 2FAuth 8.0.3 to 9.0.1

- 2FAuth 9 keeps PHP 8.4, Laravel 13, port 8000, the `/2fauth` data volume
  and every environment variable of 8.0.3. Database migrations now run at
  each container start (new `twofaccount_user_favorites` table). 9.0.1 brings
  several security fixes; see the
  [changelog](https://github.com/Bubka/2FAuth/releases/tag/v9.0.1).
- `update-module.d/10migrate_settings` runs before the restart:
  - keeps `state/key.env` (`APP_KEY`) unchanged and makes it mode 0600;
  - creates `state/passwords.env` (mode 0600);
  - imports the values of the old `state/app.env` that differ from the old
    defaults (`LOG_CHANNEL`, `LOG_LEVEL`, `SESSION_LIFETIME`, `WEBAUTHN_NAME`)
    as `TWOFAUTH_*` settings, removes the obsolete `APP_URL` environment
    variable and generates `state/app.env` again in the new format.
- The mail settings moved from `state/app.env` to `state/smarthost.env`
  with the Laravel names (the old `MAIL_MAILER=SMTP` value did not match any
  Laravel mailer).
- `TRUSTED_PROXIES` is now set: required by 2FAuth 8+ to see the HTTPS scheme
  and client address forwarded by Traefik.
- `configure-module` now restarts the containers, so new settings apply at
  once.
- Unknown `configure-module` keys from earlier releases (such as
  `LOG_LEVEL` or `SITE_OWNER`) are ignored: use the fields above.
- New installations get an `APP_KEY` in the Laravel `base64:` format.
  Existing keys stay as they are (2FAuth uses the first 32 characters of a
  plain key).

## Uninstall

To uninstall the instance:

    remove-module --no-preserve 2fauth1

## Debug

- Module environment: `runagent -m 2fauth1 env`
- Shell with the module environment: `runagent -m 2fauth1`
- Containers: `runagent -m 2fauth1 podman ps`
- Logs: `journalctl _UID=$(id -u 2fauth1)`, or the 2FAuth log files in the
  `2fauth-app` volume (`storage/logs`)
- Shell in the container: `runagent -m 2fauth1 podman exec -ti 2fauth-app sh`

## Testing

Test the module using the `test-module.sh` script:

    ./test-module.sh <NODE_ADDR> ghcr.io/geniusdynamics/2fauth:latest

The tests are made using [Robot Framework](https://robotframework.org/).

## UI translation

Translated with [Weblate](https://hosted.weblate.org/projects/ns8/).

To setup the translation process:

- add [GitHub Weblate app](https://docs.weblate.org/en/latest/admin/continuous.html#github-setup) to your repository
- add your repository to [hosted.weblate.org](https://hosted.weblate.org) or ask a NethServer developer to add it to ns8 Weblate project
