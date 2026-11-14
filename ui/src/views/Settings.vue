<!--
  Copyright (C) 2022 Nethesis S.r.l.
  SPDX-License-Identifier: GPL-3.0-or-later
-->
<template>
  <cv-grid fullWidth>
    <cv-row>
      <cv-column class="page-title">
        <h2>{{ $t("settings.title") }}</h2>
      </cv-column>
    </cv-row>
    <cv-row v-if="error.getConfiguration">
      <cv-column>
        <NsInlineNotification
          kind="error"
          :title="$t('action.get-configuration')"
          :description="error.getConfiguration"
          :showCloseButton="false"
        />
      </cv-column>
    </cv-row>
    <cv-row>
      <cv-column>
        <cv-tile light>
          <cv-form @submit.prevent="configureModule">
            <!-- web access -->
            <NsTextInput
              :label="$t('settings.2fauth_fqdn')"
              placeholder="2fauth.example.org"
              v-model.trim="host"
              class="mg-bottom maxwidth"
              :invalid-message="$t(error.host)"
              :disabled="isFormDisabled"
              ref="host"
            />
            <NsToggle
              value="letsEncrypt"
              :label="$t('settings.lets_encrypt')"
              v-model="isLetsEncryptEnabled"
              :disabled="isFormDisabled"
              class="mg-bottom"
            >
              <template slot="text-left">{{
                $t("settings.disabled")
              }}</template>
              <template slot="text-right">{{
                $t("settings.enabled")
              }}</template>
            </NsToggle>
            <NsToggle
              value="httpToHttps"
              :label="$t('settings.http_to_https')"
              v-model="isHttpToHttpsEnabled"
              :disabled="isFormDisabled"
              class="mg-bottom"
            >
              <template slot="text-left">{{
                $t("settings.disabled")
              }}</template>
              <template slot="text-right">{{
                $t("settings.enabled")
              }}</template>
            </NsToggle>

            <!-- general -->
            <h4 class="mg-bottom">{{ $t("settings.general") }}</h4>
            <NsTextInput
              :label="$t('settings.app_name')"
              placeholder="2FAuth"
              v-model.trim="appName2fa"
              class="mg-bottom maxwidth"
              :helper-text="$t('settings.app_name_helper')"
              :invalid-message="$t(error.app_name)"
              :disabled="isFormDisabled"
              ref="app_name"
            />
            <NsTextInput
              :label="$t('settings.mail_from_address')"
              :placeholder="$t('settings.mail_from_address_placeholder')"
              v-model.trim="mailFromAddress"
              class="mg-bottom maxwidth"
              :helper-text="$t('settings.mail_from_address_helper')"
              :invalid-message="$t(error.mail_from_address)"
              :disabled="isFormDisabled"
              ref="mail_from_address"
            />

            <!-- login and registration -->
            <h4 class="mg-bottom">
              {{ $t("settings.login_and_registration") }}
            </h4>
            <NsInlineNotification
              v-if="appSettingsSource === 'saved' && host"
              kind="info"
              :title="$t('settings.app_settings_saved_title')"
              :description="$t('settings.app_settings_saved_description')"
              :showCloseButton="false"
              class="maxwidth"
            />
            <NsToggle
              value="disableRegistration"
              :label="$t('settings.disable_registration')"
              v-model="disableRegistration"
              :disabled="isFormDisabled"
              class="mg-bottom"
            >
              <template slot="tooltip">{{
                $t("settings.disable_registration_tooltip")
              }}</template>
              <template slot="text-left">{{
                $t("settings.disabled")
              }}</template>
              <template slot="text-right">{{
                $t("settings.enabled")
              }}</template>
            </NsToggle>
            <NsToggle
              value="enableSso"
              :label="$t('settings.enable_sso')"
              v-model="enableSso"
              :disabled="isFormDisabled"
              class="mg-bottom"
            >
              <template slot="tooltip">{{
                $t("settings.enable_sso_tooltip")
              }}</template>
              <template slot="text-left">{{
                $t("settings.disabled")
              }}</template>
              <template slot="text-right">{{
                $t("settings.enabled")
              }}</template>
            </NsToggle>
            <template v-if="enableSso">
              <NsToggle
                value="useSsoOnly"
                :label="$t('settings.use_sso_only')"
                v-model="useSsoOnly"
                :disabled="isFormDisabled"
                class="mg-bottom"
                ref="use_sso_only"
              >
                <template slot="tooltip">{{
                  $t("settings.use_sso_only_tooltip")
                }}</template>
                <template slot="text-left">{{
                  $t("settings.disabled")
                }}</template>
                <template slot="text-right">{{
                  $t("settings.enabled")
                }}</template>
              </NsToggle>
              <NsInlineNotification
                v-if="error.use_sso_only"
                kind="error"
                :title="$t(error.use_sso_only)"
                :showCloseButton="false"
                class="maxwidth"
              />
              <NsToggle
                value="keepSsoRegistrationEnabled"
                :label="$t('settings.keep_sso_registration_enabled')"
                v-model="keepSsoRegistrationEnabled"
                :disabled="isFormDisabled"
                class="mg-bottom"
              >
                <template slot="tooltip">{{
                  $t("settings.keep_sso_registration_enabled_tooltip")
                }}</template>
                <template slot="text-left">{{
                  $t("settings.disabled")
                }}</template>
                <template slot="text-right">{{
                  $t("settings.enabled")
                }}</template>
              </NsToggle>
            </template>

            <!-- OpenID Connect -->
            <h4 class="mg-bottom">{{ $t("settings.openid_title") }}</h4>
            <p class="mg-bottom maxwidth">
              {{ $t("settings.openid_description") }}
            </p>
            <div class="mg-bottom maxwidth">
              <div class="callback-label">
                {{ $t("settings.openid_callback_url") }}
              </div>
              <NsCodeSnippet
                :copyTooltip="$t('common.copy_to_clipboard')"
                :copy-feedback="$t('common.copied_to_clipboard')"
                :feedback-aria-label="$t('common.copied_to_clipboard')"
                :wrap-text="true"
                :moreText="$t('common.show_more')"
                :lessText="$t('common.show_less')"
                hideExpandButton
                light
                >{{ callbackUrl("openid") }}</NsCodeSnippet
              >
            </div>
            <NsTextInput
              :label="$t('settings.openid_client_id')"
              v-model.trim="openidClientId"
              class="mg-bottom maxwidth"
              :helper-text="$t('settings.client_id_helper')"
              :invalid-message="$t(error.openid_client_id)"
              :disabled="isFormDisabled"
              ref="openid_client_id"
            />
            <template v-if="openidClientId">
              <NsTextInput
                :label="$t('settings.openid_client_secret')"
                type="password"
                autocomplete="new-password"
                v-model="openidClientSecret"
                class="mg-bottom maxwidth"
                :placeholder="
                  openidClientSecretSet ? $t('settings.secret_saved') : ''
                "
                :helper-text="
                  openidClientSecretSet ? $t('settings.secret_keep_helper') : ''
                "
                :invalid-message="$t(error.openid_client_secret)"
                :password-hide-label="$t('settings.hide_secret')"
                :password-show-label="$t('settings.show_secret')"
                :disabled="isFormDisabled"
                ref="openid_client_secret"
              />
              <NsTextInput
                :label="$t('settings.openid_authorize_url')"
                placeholder="https://idp.example.org/application/o/authorize/"
                v-model.trim="openidAuthorizeUrl"
                class="mg-bottom maxwidth"
                :invalid-message="$t(error.openid_authorize_url)"
                :disabled="isFormDisabled"
                ref="openid_authorize_url"
              />
              <NsTextInput
                :label="$t('settings.openid_token_url')"
                placeholder="https://idp.example.org/application/o/token/"
                v-model.trim="openidTokenUrl"
                class="mg-bottom maxwidth"
                :invalid-message="$t(error.openid_token_url)"
                :disabled="isFormDisabled"
                ref="openid_token_url"
              />
              <NsTextInput
                :label="$t('settings.openid_userinfo_url')"
                placeholder="https://idp.example.org/application/o/userinfo/"
                v-model.trim="openidUserinfoUrl"
                class="mg-bottom maxwidth"
                :invalid-message="$t(error.openid_userinfo_url)"
                :disabled="isFormDisabled"
                ref="openid_userinfo_url"
              />
              <NsToggle
                value="openidHttpVerifySslPeer"
                :label="$t('settings.openid_http_verify_ssl_peer')"
                v-model="openidHttpVerifySslPeer"
                :disabled="isFormDisabled"
                class="mg-bottom"
              >
                <template slot="tooltip">{{
                  $t("settings.openid_http_verify_ssl_peer_tooltip")
                }}</template>
                <template slot="text-left">{{
                  $t("settings.disabled")
                }}</template>
                <template slot="text-right">{{
                  $t("settings.enabled")
                }}</template>
              </NsToggle>
            </template>

            <!-- GitHub -->
            <h4 class="mg-bottom">{{ $t("settings.github_title") }}</h4>
            <p class="mg-bottom maxwidth">
              {{ $t("settings.github_description") }}
            </p>
            <div class="mg-bottom maxwidth">
              <div class="callback-label">
                {{ $t("settings.github_callback_url") }}
              </div>
              <NsCodeSnippet
                :copyTooltip="$t('common.copy_to_clipboard')"
                :copy-feedback="$t('common.copied_to_clipboard')"
                :feedback-aria-label="$t('common.copied_to_clipboard')"
                :wrap-text="true"
                :moreText="$t('common.show_more')"
                :lessText="$t('common.show_less')"
                hideExpandButton
                light
                >{{ callbackUrl("github") }}</NsCodeSnippet
              >
            </div>
            <NsTextInput
              :label="$t('settings.github_client_id')"
              v-model.trim="githubClientId"
              class="mg-bottom maxwidth"
              :helper-text="$t('settings.client_id_helper')"
              :invalid-message="$t(error.github_client_id)"
              :disabled="isFormDisabled"
              ref="github_client_id"
            />
            <NsTextInput
              v-if="githubClientId"
              :label="$t('settings.github_client_secret')"
              type="password"
              autocomplete="new-password"
              v-model="githubClientSecret"
              class="mg-bottom maxwidth"
              :placeholder="
                githubClientSecretSet ? $t('settings.secret_saved') : ''
              "
              :helper-text="
                githubClientSecretSet ? $t('settings.secret_keep_helper') : ''
              "
              :invalid-message="$t(error.github_client_secret)"
              :password-hide-label="$t('settings.hide_secret')"
              :password-show-label="$t('settings.show_secret')"
              :disabled="isFormDisabled"
              ref="github_client_secret"
            />

            <p class="mg-bottom maxwidth cli-note">
              {{ $t("settings.cli_only_note") }}
            </p>

            <cv-row v-if="error.configureModule">
              <cv-column>
                <NsInlineNotification
                  kind="error"
                  :title="$t('action.configure-module')"
                  :description="error.configureModule"
                  :showCloseButton="false"
                />
              </cv-column>
            </cv-row>
            <NsButton
              kind="primary"
              :icon="Save20"
              :loading="loading.configureModule"
              :disabled="isFormDisabled"
              >{{ $t("settings.save") }}</NsButton
            >
          </cv-form>
        </cv-tile>
      </cv-column>
    </cv-row>
  </cv-grid>
</template>

<script>
import to from "await-to-js";
import { mapState } from "vuex";
import {
  QueryParamService,
  UtilService,
  TaskService,
  IconService,
  PageTitleService,
} from "@nethserver/ns8-ui-lib";

// Characters refused in the values saved to the module environment
const UNSAFE_CHARS = /["'\\\n\r]/;
const URL_PATTERN = /^https?:\/\/[^\s"'\\]+$/;
const EMAIL_PATTERN = /^[^@\s"'\\]+@[^@\s"'\\]+$/;

export default {
  name: "Settings",
  mixins: [
    TaskService,
    IconService,
    UtilService,
    QueryParamService,
    PageTitleService,
  ],
  pageTitle() {
    return this.$t("settings.title") + " - " + this.appName;
  },
  data() {
    return {
      q: {
        page: "settings",
      },
      urlCheckInterval: null,
      host: "",
      isLetsEncryptEnabled: false,
      isHttpToHttpsEnabled: true,
      appName2fa: "2FAuth",
      mailFromAddress: "",
      disableRegistration: false,
      enableSso: true,
      useSsoOnly: false,
      keepSsoRegistrationEnabled: false,
      appSettingsSource: "saved",
      openidClientId: "",
      openidClientSecret: "",
      openidClientSecretSet: false,
      openidAuthorizeUrl: "",
      openidTokenUrl: "",
      openidUserinfoUrl: "",
      openidHttpVerifySslPeer: true,
      githubClientId: "",
      githubClientSecret: "",
      githubClientSecretSet: false,
      loading: {
        getConfiguration: false,
        configureModule: false,
      },
      error: {
        getConfiguration: "",
        configureModule: "",
        host: "",
        lets_encrypt: "",
        http2https: "",
        app_name: "",
        mail_from_address: "",
        disable_registration: "",
        enable_sso: "",
        use_sso_only: "",
        keep_sso_registration_enabled: "",
        openid_client_id: "",
        openid_client_secret: "",
        openid_authorize_url: "",
        openid_token_url: "",
        openid_userinfo_url: "",
        openid_http_verify_ssl_peer: "",
        github_client_id: "",
        github_client_secret: "",
      },
    };
  },
  computed: {
    ...mapState(["instanceName", "core", "appName"]),
    isFormDisabled() {
      return this.loading.getConfiguration || this.loading.configureModule;
    },
  },
  created() {
    this.getConfiguration();
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      vm.watchQueryData(vm);
      vm.urlCheckInterval = vm.initUrlBindingForApp(vm, vm.q.page);
    });
  },
  beforeRouteLeave(to, from, next) {
    clearInterval(this.urlCheckInterval);
    next();
  },
  methods: {
    callbackUrl(provider) {
      const host = this.host || "<host>";
      return `https://${host}/socialite/callback/${provider}`;
    },
    async getConfiguration() {
      this.loading.getConfiguration = true;
      this.error.getConfiguration = "";
      const taskAction = "get-configuration";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.getConfigurationAborted
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.getConfigurationCompleted
      );

      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          extra: {
            title: this.$t("action." + taskAction),
            isNotificationHidden: true,
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.error.getConfiguration = this.getErrorMessage(err);
        this.loading.getConfiguration = false;
        return;
      }
    },
    getConfigurationAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.getConfiguration = this.$t("error.generic_error");
      this.loading.getConfiguration = false;
    },
    getConfigurationCompleted(taskContext, taskResult) {
      const config = taskResult.output;
      this.host = config.host;
      this.isLetsEncryptEnabled = config.lets_encrypt;
      this.isHttpToHttpsEnabled = config.http2https;
      this.appName2fa = config.app_name || "2FAuth";
      this.mailFromAddress = config.mail_from_address || "";
      this.disableRegistration = !!config.disable_registration;
      this.enableSso = config.enable_sso !== false;
      this.useSsoOnly = !!config.use_sso_only;
      this.keepSsoRegistrationEnabled = !!config.keep_sso_registration_enabled;
      this.appSettingsSource = config.app_settings_source || "saved";
      this.openidClientId = config.openid_client_id || "";
      this.openidClientSecret = "";
      this.openidClientSecretSet = !!config.openid_client_secret_set;
      this.openidAuthorizeUrl = config.openid_authorize_url || "";
      this.openidTokenUrl = config.openid_token_url || "";
      this.openidUserinfoUrl = config.openid_userinfo_url || "";
      this.openidHttpVerifySslPeer =
        config.openid_http_verify_ssl_peer !== false;
      this.githubClientId = config.github_client_id || "";
      this.githubClientSecret = "";
      this.githubClientSecretSet = !!config.github_client_secret_set;

      this.loading.getConfiguration = false;
      this.focusElement("host");
    },
    validateConfigureModule() {
      this.clearErrors(this);
      let isValidationOk = true;

      const setError = (field, message) => {
        this.error[field] = message;
        if (isValidationOk) {
          this.focusElement(field);
        }
        isValidationOk = false;
      };

      if (!this.host) {
        setError("host", "common.required");
      }
      if (!this.appName2fa) {
        setError("app_name", "common.required");
      } else if (UNSAFE_CHARS.test(this.appName2fa)) {
        setError("app_name", "settings.unsafe_chars");
      }
      if (this.mailFromAddress && !EMAIL_PATTERN.test(this.mailFromAddress)) {
        setError("mail_from_address", "settings.mail_from_address_pattern");
      }
      for (const field of ["openid_client_id", "github_client_id"]) {
        const value =
          field === "openid_client_id"
            ? this.openidClientId
            : this.githubClientId;
        if (UNSAFE_CHARS.test(value)) {
          setError(field, "settings.unsafe_chars");
        }
      }
      if (this.openidClientId) {
        const urls = {
          openid_authorize_url: this.openidAuthorizeUrl,
          openid_token_url: this.openidTokenUrl,
          openid_userinfo_url: this.openidUserinfoUrl,
        };
        for (const [field, value] of Object.entries(urls)) {
          if (!value) {
            setError(field, "common.required");
          } else if (!URL_PATTERN.test(value)) {
            setError(field, "settings.url_pattern");
          }
        }
        if (!this.openidClientSecret && !this.openidClientSecretSet) {
          setError("openid_client_secret", "common.required");
        }
      }
      if (
        this.githubClientId &&
        !this.githubClientSecret &&
        !this.githubClientSecretSet
      ) {
        setError("github_client_secret", "common.required");
      }
      if (
        this.enableSso &&
        this.useSsoOnly &&
        !this.openidClientId &&
        !this.githubClientId
      ) {
        setError("use_sso_only", "settings.sso_only_requires_provider");
      }
      return isValidationOk;
    },
    configureModuleValidationFailed(validationErrors) {
      this.loading.configureModule = false;
      let focusAlreadySet = false;

      for (const validationError of validationErrors) {
        const param = validationError.parameter;
        // set i18n error message
        this.error[param] = "settings." + validationError.error;

        if (!focusAlreadySet) {
          this.focusElement(param);
          focusAlreadySet = true;
        }
      }
    },
    async configureModule() {
      const isValidationOk = this.validateConfigureModule();
      if (!isValidationOk) {
        return;
      }

      this.loading.configureModule = true;
      const taskAction = "configure-module";
      const eventId = this.getUuid();

      // register to task error
      this.core.$root.$once(
        `${taskAction}-aborted-${eventId}`,
        this.configureModuleAborted
      );

      // register to task validation
      this.core.$root.$once(
        `${taskAction}-validation-failed-${eventId}`,
        this.configureModuleValidationFailed
      );

      // register to task completion
      this.core.$root.$once(
        `${taskAction}-completed-${eventId}`,
        this.configureModuleCompleted
      );
      const res = await to(
        this.createModuleTaskForApp(this.instanceName, {
          action: taskAction,
          data: {
            host: this.host,
            lets_encrypt: this.isLetsEncryptEnabled,
            http2https: this.isHttpToHttpsEnabled,
            app_name: this.appName2fa,
            mail_from_address: this.mailFromAddress,
            disable_registration: this.disableRegistration,
            enable_sso: this.enableSso,
            use_sso_only: this.enableSso && this.useSsoOnly,
            keep_sso_registration_enabled: this.keepSsoRegistrationEnabled,
            openid_client_id: this.openidClientId,
            // empty keeps the saved secret
            openid_client_secret: this.openidClientId
              ? this.openidClientSecret
              : "",
            openid_authorize_url: this.openidAuthorizeUrl,
            openid_token_url: this.openidTokenUrl,
            openid_userinfo_url: this.openidUserinfoUrl,
            openid_http_verify_ssl_peer: this.openidHttpVerifySslPeer,
            github_client_id: this.githubClientId,
            github_client_secret: this.githubClientId
              ? this.githubClientSecret
              : "",
          },
          extra: {
            title: this.$t("settings.instance_configuration", {
              instance: this.instanceName,
            }),
            description: this.$t("settings.configuring"),
            eventId,
          },
        })
      );
      const err = res[0];

      if (err) {
        console.error(`error creating task ${taskAction}`, err);
        this.error.configureModule = this.getErrorMessage(err);
        this.loading.configureModule = false;
        return;
      }
    },
    configureModuleAborted(taskResult, taskContext) {
      console.error(`${taskContext.action} aborted`, taskResult);
      this.error.configureModule = this.$t("error.generic_error");
      this.loading.configureModule = false;
    },
    configureModuleCompleted() {
      this.loading.configureModule = false;

      // reload configuration
      this.getConfiguration();
    },
  },
};
</script>

<style scoped lang="scss">
@import "../styles/carbon-utils";
.mg-bottom {
  margin-bottom: $spacing-06;
}

.maxwidth {
  max-width: 38rem;
}

h4 {
  margin-top: $spacing-07;
}

.callback-label {
  margin-bottom: $spacing-03;
  font-weight: 600;
}

.cli-note {
  margin-top: $spacing-07;
}
</style>
