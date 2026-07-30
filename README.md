# GatewayIRAN

[![Release](https://img.shields.io/github/v/release/GatewayIRAN/certway?sort=semver&style=flat&label=release)](https://github.com/GatewayIRAN/certway/releases)
[![License](https://img.shields.io/github/license/GatewayIRAN/certway?style=flat&label=license)](https://github.com/GatewayIRAN/certway/blob/main/LICENSE)
![platform](https://img.shields.io/badge/platform-linux%20%C2%B7%20macos-6e7781?style=flat)
![binary](https://img.shields.io/badge/binary-2.1%20MB%20static-1f6feb?style=flat)
[![CI](https://github.com/GatewayIRAN/certway/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/GatewayIRAN/certway/actions/workflows/release.yml)

GatewayIRAN is a small collection around one tool: **certway** gets a TLS
certificate from Let's Encrypt — or any ACME server — onto a Linux or macOS
box and keeps it renewed, as one static binary with no runtime. This profile
is the hub for the tool and the community.

## certway

HTTPS in one command. No daemon, no Python, no OpenSSL on the box:

```bash
curl --proto '=https' --tlsv1.2 -sSfL https://github.com/GatewayIRAN/certway/releases/latest/download/certway-installer.sh | sh
```

`certway issue example.com` walks the authority for you and writes
`certs/fullchain.pem` + `certs/privkey.pem`, then `certway install` sets up
renewal (systemd timer, or cron where systemd is absent). Where certbot is a
Swiss army knife of plugins, certway is two crates that do one job: ECDSA P-256
certificates over HTTP-01/DNS-01, for nginx or by hand, with refusal instead of
guessing when an nginx edit is ambiguous.

[github.com/GatewayIRAN/certway](https://github.com/GatewayIRAN/certway) —
MIT licensed, built on `ring` and `rustls`, zero unsafe code.

## Join the channel

The 1000-member [Telegram channel @GatewayIRAN](https://t.me/GatewayIRAN) is
where releases, how-tos and comparisons are shared. It is the only known
audience for these assets.

## Security and license

Security issues: please use
[Github private vulnerability reporting](https://github.com/GatewayIRAN/certway/security/advisories/new)
— do not open a public issue.

- [CONTRIBUTING.md](https://github.com/GatewayIRAN/certway/blob/main/CONTRIBUTING.md)
- [Release notes](https://github.com/GatewayIRAN/certway/releases)

GatewayIRAN — certway · MIT · built on `ring` and `rustls`
