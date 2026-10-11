<div align="center">
  <img src="assets/banner.svg" alt="GatewayIRAN — open source collection" width="100%">
  <br><br>
  <img src="assets/typing.svg" alt="building gateways · certificates · how-tos · comparisons" height="42">
  <br><br>
  <a href="https://github.com/GatewayIRAN/certway/releases"><img src="https://img.shields.io/github/v/release/GatewayIRAN/certway?sort=semver&label=release" alt="certway latest release"></a>
  <a href="https://github.com/GatewayIRAN/certway/blob/main/LICENSE"><img src="https://img.shields.io/github/license/GatewayIRAN/certway?label=license" alt="MIT license"></a>
  <a href="https://github.com/GatewayIRAN/certway/actions/workflows/release.yml"><img src="https://img.shields.io/github/actions/workflow/status/GatewayIRAN/certway/release.yml?branch=main&label=build" alt="release build status"></a>
  <img src="https://img.shields.io/badge/platform-linux%20%C2%B7%20macos-6e7781" alt="platform linux or macos">
  <img src="https://img.shields.io/badge/binary-2.1%20MB%20static-1f6feb" alt="2.1 MB static binary">
  <img src="https://img.shields.io/badge/TLS-ACME%20%C2%B7%20Let%27s%20Encrypt-6e7781" alt="ACME, Let's Encrypt">
  <br><br>
  <b>GatewayIRAN is a hub — open tools, how-tos and comparisons for real boxes.</b><br>
  <sub><b>certway</b> is the flagship of the collection, not the whole story;<br>anything worth shipping lands in this repository family.</sub>
</div>

<img src="assets/divider.svg" alt="" width="100%">

## The collection

<table>
<tr>
<td width="50%"><img src="assets/certway-card.svg" alt="certway — HTTPS in one command: Let's Encrypt or any ACME server, HTTP-01 and DNS-01, renewal on a systemd timer or cron, ECDSA P-256 with zero unsafe code" width="100%"></td>
<td width="50%"><img src="assets/open-slots.svg" alt="open slots — new tools, how-tos and comparisons land here; the collection is not limited to one project" width="100%"></td>
</tr>
</table>

**certway** — HTTPS in one command. One static binary, no daemon, no Python,
no OpenSSL on the box:

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
Reacts to every nginx config change and reloads it for you.

The next tools, how-tos and comparisons arrive in the same shape: one problem,
one small static binary, no configuration to babysit — keep an eye on the
[channel](https://t.me/GatewayIRAN) and the
[releases feed](https://github.com/GatewayIRAN/certway/releases).

<img src="assets/stack.svg" alt="stack: Rust, Shell, GitHub Actions, nginx, systemd, ACME, TLS 1.3" width="100%">

<img src="assets/divider.svg" alt="" width="100%">

## In numbers

<img src="assets/stats.svg" alt="v1.0.0 latest release with 13 downloadable binaries — MIT license, zero unsafe code — Linux and macOS, one static binary, no runtime — about a thousand readers on Telegram" width="100%">

<img src="assets/divider.svg" alt="" width="100%">

## Join the channel

<div align="center">
  <img src="assets/cta-fa.svg" alt="به کانال تلگرام GatewayIRAN بپیوندید — تازه‌ترین ابزارها، آموزش‌ها و مقایسه‌ها — t.me/GatewayIRAN" width="100%">
  <br><br>
  <a href="https://t.me/GatewayIRAN"><img src="https://img.shields.io/badge/Telegram-Join%20%40GatewayIRAN-2AABEE?style=flat" alt="join the Telegram channel @GatewayIRAN"></a>
  <br>
  <sub>Releases, how-tos and comparisons are announced on the channel — in Persian.<br>
  «به کانال تلگرام <a href="https://t.me/GatewayIRAN">GatewayIRAN</a> بپیوندید.»</sub>
</div>

## Security and license

- 🕵️ Something looks off in a release? [Report a vulnerability privately →](https://github.com/GatewayIRAN/certway/security/advisories/new) — do not open a public issue.
- 🤝 Want to help the collection grow? [CONTRIBUTING.md →](https://github.com/GatewayIRAN/certway/blob/main/CONTRIBUTING.md)
- 📦 [Release notes →](https://github.com/GatewayIRAN/certway/releases)
- ©️ MIT — free to use, free to fork.

<img src="assets/divider.svg" alt="" width="100%">

<div align="center">
  <sub><b>GATEWAYIRAN</b> · open tools, how-tos &amp; comparisons · <a href="https://t.me/GatewayIRAN">t.me/GatewayIRAN</a> · <a href="https://gatewayiran.github.io">gatewayiran.github.io</a></sub>
</div>
