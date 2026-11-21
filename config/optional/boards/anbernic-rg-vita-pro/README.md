# RG Vita Pro vendor kernel

The vendor target uses the Rockchip 6.1 kernel.
The edge target retains its existing configuration.
Vendor-specific services and touch workarounds stay out of edge BSP packages.

Build a generic GNOME image:

```sh
./compile.sh build BOARD=anbernic-rg-vita-pro BRANCH=vendor \
  RELEASE=trixie BUILD_DESKTOP=yes DESKTOP_ENVIRONMENT=gnome DESKTOP_TIER=minimal \
  BUILD_MINIMAL=no KERNEL_CONFIGURE=no
```

Release builds use built-in DRM and USB-DP PHY drivers.
The development module deployment workflow is not part of the release image.

The first-boot setup uses landscape orientation with matching touch coordinates.
The desktop retains its normal touch mapping.

## Storage

The vendor target enables both microSD slots.
TF1 holds the system card. TF2 provides removable storage.
The tested device boots from TF1 and reads TF2 at SDR104 speed.

## Dock displays

The kernel exposes three MST streams.
Three external monitors require the internal screen off.
Two external monitors can run with the internal screen active.

Generic images leave monitor configuration to the compositor.
Optional automation requires GNOME Wayland, `gdctl`, and `python3-gi`.
The GNOME image includes these dependencies.
Other desktops keep their normal display configuration.

Enable automatic preferred modes in `/etc/vita-dock-displays.conf`:

```sh
DISABLE=0
MODE=auto
```

The helper verifies the complete layout before changing displays.
An unavailable mode or insufficient bandwidth preserves the current layout.
User settings in `~/.config/vita-dock-displays.conf` override system settings.
Read logs from `$XDG_RUNTIME_DIR/vita-dock-displays.log`.

## HP G5 triple preset

The tested connection uses these cables:

- P2720D: DisplayPort to DisplayPort.
- First P2213: HDMI to DVI.
- Second P2213: DisplayPort to DVI.

| Monitor | Native resolution | Refresh | Pixel clock | MST slots |
|---------|-------------------|---------|-------------|-----------|
| P2720D | 2560×1440 | 59.951 Hz | 241.5 MHz | 29 |
| Each P2213 | 1680×1050 | 59.949 Hz | 125 MHz | 15 |

Two HBR3 lanes provide 63 slots without DSC.
The preset uses 59 slots at RGB, 8 bits per channel.
Both P2213 monitors require custom blanking.
Their original 146.25 MHz timings exceed the link capacity with all three displays active.

List connected monitors:

```sh
gdctl show --modes
```

Replace `card0-DP-X` with the first P2213 connector.
Create the profile from that monitor's EDID:

```sh
sudo vita-dock-profile /sys/class/drm/card0-DP-X/edid \
  /etc/vita-dock-edid/P2213-A.force.bin --p2213-125mhz
```

Repeat for the second P2213. Use `P2213-B.force.bin` as its output filename.
The tool preserves each monitor's identity and rejects unsupported models or invalid EDIDs.
The service matches the exact monitor identity before applying a profile.
Captured EDIDs contain monitor serials. Keep these files private.

Install the preset and restart the profile service:

```sh
sudo install -m644 /usr/share/doc/vita-dock/hp-g5-triple.conf /etc/vita-dock-displays.conf
sudo systemctl restart vita-dock-edid.service
```

Reconnect the dock after changing the configuration.
The internal screen returns when the dock disconnects.

For configured image builds, save profiles under `$USERPATCHES_PATH/vita-dock-edid/`.
Save the preset as `$USERPATCHES_PATH/vita-dock-displays.conf`.
The board hook copies these optional inputs into the image.
Generic builds contain no captured EDIDs or personal monitor settings.

Remove the profiles and reconnect the dock to undo EDID overrides.
Set `DISABLE=1` to return layout control to the compositor.

## Other dock results

HP G5 passes two native external modes with the internal screen active.
Fairikabe passes two native modes over four HBR3 lanes in one connector orientation.
Fairikabe can omit P2720D's native timing when another DVI sink connects.
Capture a verified native EDID through a direct connection before using a restoration profile.
Use `vita-dock-profile INPUT OUTPUT.bin` to save that verified EDID.
Ordinary `.bin` profiles apply only when the preferred resolution is absent.
Custom `.force.bin` profiles also replace matching EDIDs that contain the same resolution.

Fairikabe's opposite orientation remains unreliable.
The second Fairikabe DP-to-HDMI MST hub remains unsupported in the tested cascade.
DSI shutdown can log command timeouts. The tested dock removal restores the internal screen.
These results cover the installed test kernel and matching device tree.
Fresh release images require separate hardware validation.

## Board validation

The port includes panel, touch, controls, audio, charger, and battery support.
The amplifier driver remains a separate AW87391 backport.
The vendor kernel supplies the charger and battery gauge drivers.
The patch series retains charger startup and resource fixes without duplicate driver definitions.
The charger starts charging when power connects after a battery-only boot.
The hardware test uses the existing 500 mA input limit.
The gauge reads nominal capacity from the board's battery data.
P2P addresses derive from each device's machine ID rather than a shared fixed address.

Test a fresh image on a spare card before replacing an existing installation.
Validate storage, display, touch, controls, audio, Wi-Fi, Bluetooth, charging, and battery reporting.
Validate shutdown, reboot, suspend, and wake separately.
IMU support is not included in this vendor port.
Radxa Zero 3 W/E tests cover RK3566 regressions, but do not test the RK3576 DisplayPort PHY.
