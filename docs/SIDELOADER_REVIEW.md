# Vidafix sideload helper review

Reviewed 2026-09-30. Status: **excluded from public source and releases**.

## Provenance

The local helper was adapted from the user-supplied `Plex-VIDAA-Sideload.zip`.
The original archive contains server.py, index.html, a launcher command, a README,
a Plex-named image, a TLS certificate/private key and compiled Python bytecode.
No licence, copyright notice, named author or upstream repository attribution was
found in its source or README. The user described it as a previously generated
helper, but that alone does not establish the origin of every included asset or
permission to redistribute any incorporated third-party material.

Original server.py SHA-256:
`7601529efb57cd811bcd8a23a8c70e316b60dc79a1d0ad17dad75ddbdf87a1be`

Original index.html SHA-256:
`2892bce692c5212d71d12f525f24e6388892f367cd96c5cf5f8e1d56403f1138`

A public project, [trialuser/vidaa-appstore](https://github.com/trialuser/vidaa-appstore),
describes a similar domain/DNS and Hisense API technique. Similar behaviour is
not evidence that it is the source of this archive, and its terms cannot simply
be applied to the supplied helper. Exact upstream provenance remains unresolved.

## Behaviour observed in the local adapted source

- Python standard library only; no package download, analytics client or Plex
  token input was found in the reviewed source.
- Listens on all IPv4 interfaces for UDP DNS port 53 and HTTPS port 443.
- Answers requests for vidaahub.com using the helper's LAN IP; forwards other
  DNS requests to public Cloudflare/Google resolvers. This discloses those DNS
  queries to the selected upstream resolver while a device uses the helper.
- The local HTTPS handler restricts responses to the installer page and icon.
  The PEM files are not allowed HTTP paths in the adapted handler.
- The page calls Hisense_installApp / Hisense_uninstallApp and platform refresh
  APIs. It also requests allowance for the configured HTTP app host.
- Existing files contain a deployment-specific server address and a self-signed
  TLS key/certificate. They have not been generalized or repackaged for public use.
- The original ZIP includes compiled bytecode; this review inspected text source,
  not a decompilation/provenance verification of that bytecode.

No configured Plex-token match was found in the adapted helper or the existing
project deployment/sideload ZIPs. A certificate private key was found in the
local helper and the historical sideload ZIPs. Those files remain local; do not
publish them or reuse the key as production credentials. This is a bounded
source/data review, not a penetration test or proof of vendor authorization.

## Release decision

The complete local `vidaa-installer/` folder is ignored by Git and omitted by the
public export allowlist. Existing personal ZIPs and working installations are
preserved. The project licence does not claim rights over this excluded helper.

To release a helper later, establish the exact source/licence and asset rights,
preserve all required notices, remove deployment-specific settings and bytecode,
generate credentials per installation, and separately review the vendor terms
and installation method. Working on one TV is not evidence of permission or
compatibility on another. The public README documents browser access and the
limitation rather than promising an included TV installer.

## Separate upstream guidance — 2026-10-03

See [SIDELOADING.md](SIDELOADING.md) for a separately obtained upstream alternative
and Vidafix app/icon configuration. No explicit licence file was visible in its
reviewed root. Do not treat source visibility as redistribution permission.
No upstream code, executable, certificate or private key has been downloaded
into or bundled with the public release by this review. The alternative uses a
different launcher identifier and is not the previously tested helper.

## Public Vidafix add-on - 2026-10-03

The public export now includes sideload-addon/configure_vidafix.py, an original
standalone installer-page template and READ_ME.txt under MIT. These are newly
written files, not a redistributed copy of the supplied/upstream server. The
configuration script backs up a separately downloaded tool's config, preserves
server.py/TLS paths and generates only a Vidafix page/settings. Generated personal
files belong outside this public source folder. The DNS/HTTPS server and all
credentials remain excluded. Offline checks do not prove this combination works
on the TV; the previous helper's hardware result does not transfer to this one.
