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
Both HP G5 connector orientations and repeated reconnection pass.
Switching from direct HDMI to HP G5 preserves all three native modes.

For configured image builds, save profiles under `$USERPATCHES_PATH/vita-dock-edid/`.
Save the preset as `$USERPATCHES_PATH/vita-dock-displays.conf`.
The board hook copies these optional inputs into the image.
Generic builds contain no captured EDIDs or personal monitor settings.

Remove the profiles and reconnect the dock to undo EDID overrides.
Set `DISABLE=1` to return layout control to the compositor.

## Other display results

HP G5 passes two native external modes with the internal screen active.
Direct USB-C DP passes P2720D at 2560x1440 in both orientations over four HBR2 lanes.
Direct HDMI passes P2213 at 1680x1050 through HDMI-to-DVI.
The first HDMI connection can miss EDID and use a 1080p fallback. Reconnection restores native P2213 detection.
The tested USB-C-to-HDMI cable with HDMI-to-DVI and DVI cabling produces no picture on P2213.

Fairikabe passes two native modes over four HBR3 lanes in one connector orientation.
Fairikabe can omit P2720D's native timing when another DVI sink connects.
Capture a verified native EDID through a direct connection before using a restoration profile.
Use `vita-dock-profile INPUT OUTPUT.bin` to save that verified EDID.
Ordinary `.bin` profiles apply only when the preferred resolution is absent.
Custom `.force.bin` profiles also replace matching EDIDs that contain the same resolution.

Fairikabe's opposite orientation remains unreliable.
The second Fairikabe DP-to-HDMI MST hub remains unsupported in the tested cascade.
DSI shutdown can log command timeouts. The tested dock removal restores the internal screen.

## Board validation

The port includes panel, touch, controls, audio, charger, and battery support.
The amplifier driver remains a separate AW87391 backport.
The vendor kernel supplies the charger and battery gauge drivers.
The patch series retains charger startup and resource fixes without duplicate driver definitions.
The charger starts charging when power connects after a battery-only boot.
The hardware test uses the existing 500 mA input limit.
The gauge reads nominal capacity from the board's battery data.
P2P addresses derive from each device's machine ID rather than a shared fixed address.

Hardware tests cover RG Vita Pro with GNOME Wayland and the vendor 6.1.172 kernel.

| Function | Validated result |
|----------|------------------|
| Boot and storage | Fresh generic image; TF1 boot; TF2 SDR104 read. |
| Display and touch | First-boot setup, desktop orientation, touch, and dock removal. |
| Controls | 17 gamepad keys, Home, stick clicks, and four stick axes. |
| Audio | Internal left/right speakers; MD 44067 A2DP/SBC stereo at 48 kHz. |
| Network | Wi-Fi, SSH, and Bluetooth pairing. |
| Power | Nominal 5 Ah reporting, charging after battery boot, shutdown, and reboot. |

Armbian disables suspend by default.
Opt-in deep and s2idle attempts fail in the RMI4 touch driver.
The failed attempt leaves touch disabled until reboot.
Rumble and analog Z/RZ events remain unverified.
IMU support is not included in this vendor port.
Other RK35xx boards have no hardware regression results.
