# Vidafix portable folder

This package contains the same app for Windows and Linux. Extract the whole
ZIP before running it. Python and first-time dependency downloads are required;
this is a portable source folder, not a self-contained EXE or offline runtime.

## Windows

1. Install Python 3.9+ from python.org (a supported version such as 3.12 is
   recommended), with pip and the Python launcher or Python on PATH.
2. Extract `vidafix` to a writable, permanent folder outside cloud sync.
3. Double-click **Setup-Windows.cmd**.
4. Open **config.ini** in Notepad. Set the Plex server and your own token.
   Use `http://127.0.0.1:32400` for Plex on this PC or its private LAN address
   when hosted elsewhere. Never share the configured file.
5. Double-click **Start-Vidafix.cmd** and leave its window open.
6. Open `http://127.0.0.1:8765/` locally. From the TV use the hosting PC's
   LAN IP instead of 127.0.0.1. Allow TCP 8765 only on your trusted private LAN.

## Linux Mint

Install Python/venv/pip if needed:

```sh
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

Open a terminal inside the extracted `vidafix` folder:

```sh
sh Setup-Linux.sh
nano config.ini
sh Start-Linux.sh
```

Set the Plex address/token before starting. Use the same local/TV URL rules
as Windows. The host must remain powered on and awake.

## Moving or sharing the app

Share the original clean ZIP, not a configured working folder. Your working
folder develops private config.ini, artwork cache, logs and a local .venv.
These must not be sent with a public copy. The supplied ZIP contains none of them.

After moving between machines/platforms, create a new local virtual environment
using setup; a .venv is tied to its platform and path. Preserve your private
configuration separately if moving your own installation. If automatic startup
was installed, remove/reinstall it for the new location. Foreground launchers
find their folder automatically; no fixed personal paths are built in.

Read [README.md](README.md) for token instructions, playback limitations,
Windows sign-in startup, Linux systemd startup, updates and troubleshooting.
TV sideload tooling is excluded pending redistribution review; an existing
TV tile works if its app host address is unchanged. Nothing in setup changes
your firewall, registers startup or uploads to GitHub automatically.
