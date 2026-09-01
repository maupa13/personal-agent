#!/usr/bin/env bash
set -euo pipefail

SMTP_DOMAIN="${SMTP_DOMAIN:?SMTP_DOMAIN is required}"
SMTP_HOSTNAME="${SMTP_HOSTNAME:?SMTP_HOSTNAME is required}"
SMTP_ALLOWED_NETWORKS="${SMTP_ALLOWED_NETWORKS:-127.0.0.0/8 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 [::1]/128}"
SMTP_DKIM_SELECTOR="${SMTP_DKIM_SELECTOR:-mail}"
SMTP_ENABLE_DKIM="${SMTP_ENABLE_DKIM:-1}"
SMTP_SUPPORT_EMAIL="${SMTP_SUPPORT_EMAIL:-support@${SMTP_DOMAIN}}"
TRUSTED_HOSTS="$(printf '%s\n' ${SMTP_ALLOWED_NETWORKS})"
SUPPORT_LOCALPART="${SMTP_SUPPORT_EMAIL%@*}"
SUPPORT_DOMAIN="${SMTP_SUPPORT_EMAIL#*@}"

DKIM_BASE="/var/lib/opendkim"
DKIM_DIR="${DKIM_BASE}/keys/${SMTP_DOMAIN}"
DKIM_PRIVATE_KEY="${DKIM_DIR}/${SMTP_DKIM_SELECTOR}.private"
DKIM_DNS_FILE="${DKIM_DIR}/${SMTP_DKIM_SELECTOR}.txt"

mkdir -p "${DKIM_DIR}" /etc/opendkim /run/opendkim /var/mail/support/Maildir/{cur,new,tmp}
chown -R opendkim:opendkim "${DKIM_BASE}" /run/opendkim
chown -R support:support /var/mail/support

if [[ "${SMTP_ENABLE_DKIM}" == "1" && ! -s "${DKIM_PRIVATE_KEY}" ]]; then
  rm -f "${DKIM_DIR}/${SMTP_DKIM_SELECTOR}.private" "${DKIM_DIR}/${SMTP_DKIM_SELECTOR}.txt"
  opendkim-genkey -b 2048 -D "${DKIM_DIR}" -d "${SMTP_DOMAIN}" -s "${SMTP_DKIM_SELECTOR}"
  chown opendkim:opendkim "${DKIM_DIR}/${SMTP_DKIM_SELECTOR}.private" "${DKIM_DIR}/${SMTP_DKIM_SELECTOR}.txt"
  chmod 600 "${DKIM_DIR}/${SMTP_DKIM_SELECTOR}.private"
fi

if [[ "${SMTP_ENABLE_DKIM}" == "1" ]]; then
cat > /etc/opendkim.conf <<EOF
Syslog yes
UMask 002
Canonicalization relaxed/simple
Mode s
SubDomains no
OversignHeaders From
Socket inet:8891@127.0.0.1
PidFile /run/opendkim/opendkim.pid
KeyTable /etc/opendkim/KeyTable
SigningTable refile:/etc/opendkim/SigningTable
ExternalIgnoreList /etc/opendkim/TrustedHosts
InternalHosts /etc/opendkim/TrustedHosts
EOF

cat > /etc/opendkim/KeyTable <<EOF
${SMTP_DKIM_SELECTOR}._domainkey.${SMTP_DOMAIN} ${SMTP_DOMAIN}:${SMTP_DKIM_SELECTOR}:${DKIM_PRIVATE_KEY}
EOF

cat > /etc/opendkim/SigningTable <<EOF
*@${SMTP_DOMAIN} ${SMTP_DKIM_SELECTOR}._domainkey.${SMTP_DOMAIN}
EOF

cat > /etc/opendkim/TrustedHosts <<EOF
127.0.0.1
localhost
${TRUSTED_HOSTS}
EOF
fi

postconf -e "compatibility_level = 3.6"
postconf -e "myhostname = ${SMTP_HOSTNAME}"
postconf -e "mydomain = ${SMTP_DOMAIN}"
postconf -e 'myorigin = $mydomain'
postconf -e "inet_interfaces = all"
postconf -e "inet_protocols = ipv4"
postconf -e 'home_mailbox = Maildir/'
postconf -e "mydestination = localhost, localhost.localdomain, ${SMTP_HOSTNAME}, ${SUPPORT_DOMAIN}"
postconf -e "mynetworks = ${SMTP_ALLOWED_NETWORKS}"
postconf -e "smtpd_recipient_restrictions = permit_mynetworks,reject_unauth_destination"
postconf -e "smtpd_relay_restrictions = permit_mynetworks,reject_unauth_destination"
postconf -e "smtp_tls_security_level = may"
postconf -e "smtp_tls_loglevel = 1"
postconf -e "smtpd_tls_security_level = none"
if [[ "${SMTP_ENABLE_DKIM}" == "1" ]]; then
  postconf -e "milter_default_action = accept"
  postconf -e "milter_protocol = 6"
  postconf -e "smtpd_milters = inet:127.0.0.1:8891"
  postconf -e "non_smtpd_milters = inet:127.0.0.1:8891"
else
  postconf -e "smtpd_milters ="
  postconf -e "non_smtpd_milters ="
fi
postconf -e "maillog_file = /dev/stdout"
postconf -e "mailbox_size_limit = 0"
postconf -e "recipient_delimiter = +"
postconf -e "append_dot_mydomain = no"
postconf -e "readme_directory = no"

cat > /etc/aliases <<EOF
postmaster: ${SUPPORT_LOCALPART}
root: ${SUPPORT_LOCALPART}
${SUPPORT_LOCALPART}: support
EOF
newaliases

if [[ "${SMTP_ENABLE_DKIM}" == "1" ]]; then
  echo "[smtp] DKIM DNS record for ${SMTP_DOMAIN}:"
  tr -d '\n' < "${DKIM_DNS_FILE}" | sed 's/[[:space:]]\+/ /g'
  echo
  opendkim -f -x /etc/opendkim.conf &
else
  echo "[smtp] DKIM disabled; starting local relay without signing"
fi
exec postfix start-fg
