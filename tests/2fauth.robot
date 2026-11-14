*** Settings ***
Library    SSHLibrary
Library    Collections

*** Variables ***
${HOST}             2fauth.example.org
${OPENID_SECRET}    robot-oidc-S3cret-value
${CONFIG}           {"host":"${HOST}","http2https":true,"lets_encrypt":false,
...                 "app_name":"2FAuth Robot","mail_from_address":"2fauth@example.org",
...                 "enable_sso":true,"use_sso_only":false,"disable_registration":false,
...                 "keep_sso_registration_enabled":true,
...                 "openid_authorize_url":"https://idp.example.org/application/o/authorize/",
...                 "openid_token_url":"https://idp.example.org/application/o/token/",
...                 "openid_userinfo_url":"https://idp.example.org/application/o/userinfo/",
...                 "openid_client_id":"2fauth-robot","openid_client_secret":"${OPENID_SECRET}",
...                 "openid_http_verify_ssl_peer":true,
...                 "github_client_id":"","github_client_secret":"",
...                 "app_timezone":"Europe/Rome","session_lifetime":240}

*** Test Cases ***
Check if 2fauth is installed correctly
    ${output}  ${rc} =    Execute Command    add-module ${IMAGE_URL} 1
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    &{output} =    Evaluate    ${output}
    Set Suite Variable    ${module_id}    ${output.module_id}

Check if 2fauth can be configured
    ${stdout}  ${stderr}  ${rc} =    Execute Command    api-cli run module/${module_id}/configure-module --data '${CONFIG}'
    ...    return_rc=True  return_stderr=True
    Log    ${stderr}
    Should Be Equal As Integers    ${rc}  0

Check if the configuration is returned without secrets
    ${output}  ${rc} =    Execute Command    api-cli run module/${module_id}/get-configuration
    ...    return_rc=True
    Should Be Equal As Integers    ${rc}  0
    Should Not Contain    ${output}    ${OPENID_SECRET}
    ${config} =    Evaluate    json.loads($output)    modules=json
    Should Be Equal    ${config}[host]    ${HOST}
    Should Be Equal    ${config}[app_name]    2FAuth Robot
    Should Be Equal    ${config}[openid_client_id]    2fauth-robot
    Should Be Equal    ${config}[openid_token_url]    https://idp.example.org/application/o/token/
    Should Be Equal    ${config}[app_timezone]    Europe/Rome
    Should Be Equal As Integers    ${config}[session_lifetime]    240
    Should Be True    ${config}[openid_client_secret_set]
    Should Not Be True    ${config}[github_client_secret_set]
    Should Be True    ${config}[keep_sso_registration_enabled]
    Dictionary Should Not Contain Key    ${config}    openid_client_secret
    Dictionary Should Not Contain Key    ${config}    github_client_secret

Check if the secrets file is private
    ${mode} =    Execute Command    stat -c %a /home/${module_id}/.config/state/passwords.env
    Should Be Equal    ${mode}    600
    ${rc} =    Execute Command    grep -q '${OPENID_SECRET}' /home/${module_id}/.config/state/environment
    ...    return_rc=True  return_stdout=False
    Should Not Be Equal As Integers    ${rc}  0

Check if 2fauth works as expected
    Wait Until Keyword Succeeds    15 min    15 sec    2fauth answers through Traefik

Check if 2fauth is removed correctly
    ${rc} =    Execute Command    remove-module --no-preserve ${module_id}
    ...    return_rc=True  return_stdout=False
    Should Be Equal As Integers    ${rc}  0

*** Keywords ***
2fauth answers through Traefik
    ${code} =    Execute Command    curl -k -s -o /dev/null -w '\%{http_code}' --resolve ${HOST}:443:127.0.0.1 https://${HOST}/
    Should Match Regexp    ${code}    ^(2\\d\\d|3\\d\\d|401|403)$
