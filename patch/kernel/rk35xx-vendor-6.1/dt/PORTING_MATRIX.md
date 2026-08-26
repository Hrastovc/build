# RG Vita Pro: edge → vendor DT porting matrix

Tracks every board-level node from the **edge** (mainline) device tree against the current **vendor** (rk-6.1 BSP) device tree.

| Tree | Path |
|------|------|
| Edge (source of truth for wiring) | [`patch/kernel/archive/rockchip64-7.1/dt/rk3576-anbernic-rg-vita-pro.dts`](../../archive/rockchip64-7.1/dt/rk3576-anbernic-rg-vita-pro.dts) |
| Vendor (current) | [`rk3576-anbernic-rg-vita-pro.dts`](rk3576-anbernic-rg-vita-pro.dts) |
| Vendor shared includes | `rk3576.dtsi`, `rk3576-rk806.dtsi`, `rk3576-linux.dtsi` (from `linux-rockchip` `rk-6.1-rkr5.1`) |

Status legend:

| Status | Meaning |
|--------|---------|
| **done** | Present in vendor DT (or shared include) with equivalent role |
| **partial** | Present but incomplete, renamed, differently wired, or missing properties |
| **missing** | Not in vendor board DT yet |
| **n/a** | Edge-only construct / not applicable to vendor layout |
| **blocker** | Needs driver backport and/or BSP binding rewrite before a faithful port |

---

## Summary

| Area | Done | Partial | Missing | Blockers |
|------|------|---------|---------|----------|
| Root / aliases / chosen / memory | 3 | 1 | 1 | — |
| Fixed / GPIO regulators | 5 | 1 | 2 | — |
| RK806 PMIC + rails | — | 1 | — | — |
| CPU / GPU / thermal / PHY basics | 5 | 2 | 1 | — |
| Storage (eMMC / SD / SDIO) | 2 | 1 | 1 | — |
| UART / USB host basics | 4 | 1 | — | — |
| Display / backlight / VOP / DSI | 11 | — | 1 | — |
| Input (keys, ADC, touch, joypad) | 5 | — | 1 | IMU still missing |
| Audio | 7 | — | — | HDMI SAI6 sound card |
| Power (charger / gauge / battery / Type-C) | 4 | — | 1 | reboot-mode still missing |
| WiFi / BT / PCIe | 4 | — | — | RTL8822CS PCIe + UART BT |
| Pinctrl groups | 8 | — | ~6 groups | — |
| Misc (reboot-mode, IMU placeholder) | — | — | 2 | — |

DSI panel path is ported (`rocknix,generic-dsi` backported + BSP VOP/DSI routing). PCIe WiFi + UART BT (RTL8822CS), Type-C DP altmode, and HDMI TX are ported. Remaining gaps: reboot-mode, IMU. Hardware parity with edge is **nearly** complete.

---

## 1. Includes and structure

| Edge | Vendor | Status | Notes |
|------|--------|--------|-------|
| `#include "rk3576.dtsi"` only | `rk3576.dtsi` + `rk3576-rk806.dtsi` + `rk3576-linux.dtsi` | **partial** | Vendor PMIC and Linux aliases/reserved-memory come from includes |
| Inline RK806 under `&i2c1` | Shared `rk3576-rk806.dtsi` | **done** | Intentional BSP style |
| Mainline binding headers (`vop2.h`, `usb/pd.h`, `leds/common.h`, …) | Minimal (`gpio.h`, `rockchip.h`) | **partial** | Re-add as nodes are ported |
| — | `/delete-node/ &fiq_debugger` | **done** | Keeps `ttyS0` / Armbian `SERIALCON` |
| — | `/delete-node/ chosen` then re-add | **done** | Drops android bootargs from `rk3576-linux.dtsi` |

---

## 2. Root node

| Edge node / property | Compatible / role | Vendor | Status | Notes |
|----------------------|-------------------|--------|--------|-------|
| `model` / `compatible` | board id | same | **done** | |
| `aliases` mmc0=sdhci, mmc1=sdmmc, mmc2=sdio | boot order | via `rk3576-linux.dtsi` | **done** | Same mapping as edge |
| `chosen` `stdout-path = serial0:1500000n8` | console | present | **done** | |
| `reserved-memory` / `linux,cma` (256 MiB) | CMA | vendor uses drm-logo / ramoops from `rk3576-linux.dtsi` | **partial** | No edge-style CMA pool; may matter for display later |
| `hdmi_con` | `hdmi-connector` type c | n/a | **n/a** | Vendor HPD via PHY/pins; no external connector graph |
| `adc_keys_home` | `adc-keys` SARADC ch1 HOME | present | **done** | |
| `adc_keys_play` | `adc-keys` SARADC ch3 PLAY | present | **done** | |
| `hp_amp` | `simple-audio-amplifier` gpio0 PC3 | present | **done** | |
| `backlight` | `pwm-backlight` `&pwm1_6ch_3` | present | **done** | Same brightness curve as edge |
| `battery` | `simple-battery` 5000 mAh | present | **done** | Feeds sgm41542 `monitored-battery` |
| `gamepad_keys` | `gpio-keys` face/D-pad/shoulders | present | **done** | Analog sticks on `&spi1` SPI MCU |
| `gpio_keys` | volume up/down | present | **done** | |
| `gpio_leds` | amber/green/red | present | **done** | green=PA5, amber=PA4, red=PA6 |
| `rfkill` | `rfkill-gpio` wifi en gpio0 PC6 | present | **done** | Needs `CONFIG_RFKILL_GPIO=y` |
| `sound` | `simple-audio-card` es8388 + amps | present | **done** | Card name `rockchip,es8388-codec` for `vita-jack-switch` |

---

## 3. Board regulators (root)

| Edge label | Type | Key wiring | Vendor | Status | Notes |
|------------|------|------------|--------|--------|-------|
| `vcc_3v8_sys` | fixed 3.8 V always-on | system rail | `vcc_sys` @ 3.8 V | **partial** | Renamed so `rk3576-rk806.dtsi` `vcc*-supply` resolves |
| `vcc_1v1_nldo_s3` | fixed 1.1 V | vin ← sys | present (vin ← `vcc_sys`) | **done** | |
| `vcc_2v0_pldo_s3` | fixed 2.0 V | vin ← sys | present | **done** | |
| `vcc_1v8_s0` | fixed 1.8 V | vin ← `vcc_1v8_s3` | present | **done** | |
| `vcc3v3_sd_s0` | fixed 3.3 V + gpio0 PB6 | SD VCC | `vcc_3v3_sd_s0` (+ `vin-supply` `vcc_3v3_s3`, boot-on) | **partial** | Name `vcc_3v3_sd_s0` vs edge `vcc3v3_sd_s0`; pinctrl `sd_s0_pwr` vs `vcc_3v3_sd_s0_h` |
| `vcc_sdio` | `regulator-gpio` gpio0 PB4 1.8/3.3 | SDIO IO | — | **missing** | Used by edge `&sdio` `vqmmc` |
| `vcc_wifi` | fixed 3.3 V gpio1 PD2 | PCIe WiFi power | present | **done** | |
| `vdd_lcd` | fixed 3.3 V gpio0 PB0 | panel / touch VDD | present | **done** | |

---

## 4. RK806 PMIC (`&i2c1` / include)

| Edge | Vendor | Status | Notes |
|------|--------|--------|-------|
| Full inline `pmic@23` + DVS pinmux + all DCDC/PLDO/NLDO | `rk3576-rk806.dtsi` | **partial** | Rails exist under BSP names; not re-validated line-by-line vs Vita edge voltages/suspend |
| Supplies from `vcc_3v8_sys` | Supplies from `vcc_sys` | **done** | Same 3.8 V intent |
| `system-power-controller` | BSP include | **partial** | Confirm BSP property set |
| Edge SARADC vref `vcca1v8_pldo2_s0` | Vendor SARADC vref `vcca_1v8_s0` | **partial** | Different rail than edge |

Individual edge regulator labels (`vdd_cpu_*`, `vccio_sd_s0`, `vcca_3v3_s0`, …) are expected from the include; treat as **done via include** unless bring-up shows a mismatch.

---

## 5. CPUs, GPU, PHYs, thermal

| Edge | Vendor | Status | Notes |
|------|--------|--------|-------|
| `&cpu_b0`…`&cpu_b3` cpu-supply | only `&cpu_b0` | **partial** | BSP often only sets cluster lead; extend if needed |
| `&cpu_l0`…`&cpu_l3` cpu-supply | only `&cpu_l0` | **partial** | same |
| `&gpu` mali-supply + `resets = <&cru SRST_GPU>` | mali-supply only | **partial** | Reset prop may be mainline-specific |
| `&combphy0_ps` okay | okay | **done** | |
| `&saradc` okay + vref | okay + vref | **partial** | vref rail differs (see PMIC) |
| `&tsadc` | okay | **done** | Vendor-only enable (not in edge board file) |
| `&mipidcphy` okay | `&mipidcphy0` okay | **done** | Vendor label is `mipidcphy0` |

---

## 6. Storage

| Edge | Vendor | Status | Notes |
|------|--------|--------|-------|
| `&sdhci` eMMC HS400, `/delete-property/ supports-cqe` | same idea + max-freq 200 MHz | **done** | CQE disable preserved |
| `&sdmmc` SD, vmmc `vcc3v3_sd_s0`, vqmmc `vccio_sd_s0` | vmmc `vcc_3v3_sd_s0`, vqmmc `vccio_sd_s0` | **partial** | Supply label rename; UHS props slightly fewer on vendor |
| `&sdio` configured as **removable SD** (`no-sdio`, det, `vcc_sdio`) | — | **missing** | Edge naming is confusing; second SD slot / WiFi slot TBD |

---

## 7. UART / USB (minimal host)

| Edge | Vendor | Status | Notes |
|------|--------|--------|-------|
| `&uart0` okay | okay | **done** | |
| `&uart6` + `realtek,rtl8822cs-bt` | — | **missing** | BT |
| `&u2phy0` / `&u2phy0_otg` okay | okay | **done** | |
| `&usb_drd0_dwc3` `dr_mode = "otg"` + role-switch + Type-C ports | `dr_mode = "host"` only | **partial** | No role-switch / DP alt-mode yet |
| `&usbdp_phy` mode/orientation switch + SBU GPIOs | — | **missing** | |
| Type-C graph (`husb311` connector ports) | — | **missing** | |

---

## 8. Display / video

| Edge | Vendor | Status | Notes |
|------|--------|--------|-------|
| `&dsi` + `panel@0` `rocknix,generic-dsi` | present + driver backport | **done** | Patch `board-rg-vita-pro-drm-panel-rocknix-generic-dsi.patch`; `CONFIG_DRM_PANEL_ROCKNIX_GENERIC_DSI=y` |
| Panel enable gpio0 PB1, reset gpio0 PB5, rotation 270 | same | **done** | |
| `&dsi_in` / `&dsi_out` endpoints | BSP `&dsi_in_vp1` + board `ports/port@1` | **done** | Vendor prewires VP→DSI; do not use mainline endpoint style |
| `&backlight` + `&pwm1_6ch_3` | present | **done** | |
| `&vop` + clock parents/rates | `&vop` + `&vp1` DCLK parent | **done** | BSP clock setup |
| `&vop_mmu` | okay | **done** | |
| `&route_dsi` (vendor-only) | okay, connect `vp1_out_dsi` | **done** | |
| `&mipidcphy` / `mipidcphy0` | `&mipidcphy0` | **done** | |
| `&vp0` HDMI endpoint | present | **done** | `&hdmi_in_vp0` + `&route_hdmi` → `vp0_out_hdmi` |
| `&vp2` DP0 endpoint | present | **done** | `&dp0_in_vp{0,2}` + `&route_dp0` → `vp2_out_dp0` |
| USB-C MST `&dp0` / `&dp1` / `&dp2` | present | **done** | Three dw-dp stream encoders; `dp0`+`dp1`+`dp2` okay; overlapping VP endpoints for GNOME |
| `max-link-rate = <5400>` (HBR2) | present | **done** | Avoids MST FIFO overflow on 2-lane dock; SST 4-lane 1440p still OK |
| `display_subsystem` HDMI PHY PLL | present | **done** | Exact DP pixel clocks (e.g. 2560×1440 @ 241.5 MHz) |
| `&hdmi` / `&hdmi_in` / `&hdmi_out` / `hdmi_con` | `&hdmi` + `&hdmi_in_vp0` | **done** | BSP style (no `hdmi_out` / connector node) |
| `&hdmi_sound` / `&hdptxphy` / `&dp` | present | **done** | `hdmi_sound` + `&hdptxphy_hdmi` + `&dp`/`&dp0`/`&dp1`/`&dp2` |

---

## 9. Input

| Edge | Vendor | Status | Notes |
|------|--------|--------|-------|
| `gamepad_keys` (16 buttons) | present | **done** | Pure gpio-keys; analog sticks on SPI MCU |
| `gpio_keys` volume | — | **missing** | |
| `adc_keys_home` / `adc_keys_play` | — | **missing** | Needs working `&saradc` (partially on) |
| `&i2c0` `rmi4-i2c@70` touch | present | **done** | `CONFIG_RMI4_CORE/I2C/F12=y` |
| `&spi1` `anbernic,spi-mcu-joypad` | present | **done** | `board-rg-vita-pro-spi-mcu-joypad-*.patch`; `CONFIG_JOYSTICK_SPI_MCU_JOYPAD=y` |
| `&i2c2` ICM42607 placeholder | — | **missing** | Driver still pending upstream even on edge |

---

## 10. Audio

| Edge | Vendor | Status | Notes |
|------|--------|--------|-------|
| `sound` simple-audio-card `rockchip,es8388-codec` | present | **done** | Userspace expects this card name |
| `&i2c3` `es8388@10` | present | **done** | BSP `&mclkout_sai1` MCLK @ 12.288 MHz |
| `&i2c3` `aw87391@58` / `@5b` | present | **done** | Driver backport `board-rg-vita-pro-asoc-aw87391.patch` |
| `hp_amp` simple amp | present | **done** | `CONFIG_SND_SOC_SIMPLE_AMPLIFIER=y` |
| `&sai1` I2S pins | present | **done** | `sai1m0_*` |
| `&sai6` / `&sai7` | `&sai6` | **done** | HDMI audio via `hdmi_sound` → SAI6; sai7 unused |

**Speakers verified** on vendor 6.1 — vendor ES8328 driver exposes `Left/Right Mixer Playback Switch` (default off); `asound.state.anbernic-rg-vita-pro` enables them on boot. Default PCM lowered to ~67% so first test is not full blast.

---

## 11. Power / Type-C / RTC

| Edge | Vendor | Status | Notes |
|------|--------|--------|-------|
| `battery` simple-battery | present | **done** | 5000 mAh Li-ion parameters from edge |
| `&i2c6` `sgm41542@3b` | present | **done** | `board-rg-vita-pro-sgm41542.patch`; `vbus5v0_typec` for Type-C later |
| `&i2c6` `husb311@4e` Type-C | present | **done** | OTG host/device + DP altmode via `usbdp_phy` |
| `&i2c6` `hym8563@51` RTC | present | **done** | |
| `&i2c6` `cw221X@64` fuel gauge | present | **done** | `board-rg-vita-pro-cw221x.patch` + battery profile blob |
| `&pmu0_grf` `syscon-reboot-mode` (maskrom) | — | **missing** | Handy for sealed units |

---

## 12. WiFi / Bluetooth / PCIe

| Edge | Vendor | Status | Notes |
|------|--------|--------|-------|
| `rfkill` wifi enable | present | **done** | |
| `vcc_wifi` | present | **done** | |
| `&pcie0` reset gpio2 PB4, vpcie ← wifi | present | **done** | `CONFIG_RTW88_8822CS=y`; `phys = combphy0_ps` |
| `&uart6` BT child | present | **done** | `realtek,rtl8822cs-bt` via HCI H5 |

---

## 13. Pinctrl groups

| Edge group / labels | Vendor | Status |
|---------------------|--------|--------|
| `led_*` | present | **done** |
| `sd_s0_pwr` / `vcc_3v3_sd_s0_h` | `sd_s0_pwr` | **done** (renamed) |
| `audio` (`hp_amp_enable_h`, `hp_det`) | present | **done** |
| `buttons` / `button_pins` | present | **done** |
| `charger` / `charger_ok` | present | **done** |
| `display` (`lcd_enable`, `lcd_rst`) | present | **done** |
| `pcie` / `pcie0_perstn` | present | **done** |
| `regulator` (`vdd_lcd_h`, `vcc_wifi_h`; others still missing) | partial | **partial** |
| `rtc` / `hym8563_int` | present | **done** |
| `touch` | present | **done** |
| `usb` (`usbc_int`, SBU) | present | **done** |
| `volume-keys` | present | **done** |
| `wifi` / `wifi_en_h` | present | **done** |
| `bluetooth` BT GPIOs | present | **done** |

`pmic_pins` comes from SoC pinctrl include on vendor (not redeclared in board file).

---

## Suggested porting order

1. ~~Display path (DSI + backlight + VOP)~~ **done**
2. ~~PCIe WiFi + UART BT + rfkill / `vcc_wifi`~~ **done**
3. ~~GPIO keys + volume + ADC keys~~ **done**
4. ~~`hym8563` RTC on `&i2c6`~~ **done**
5. ~~Touch (`rmi4-i2c`)~~ **done** — `CONFIG_RMI4_I2C=m` (deferred). Shares `vdd_lcd` with the panel (no touch `vdd-supply`; rail `always-on`). `vita-touch-defer.conf` blacklists early autoload; `vita-panel-touch-fix.service` `insmod`s touch after first modeset, then soft blank/unblank.
6. ~~Audio: ES8388 + simple-audio-card + AW87391 amps~~ **done** — speakers confirmed; headphones/`vita-jack-switch` still to re-check when convenient.
7. ~~Type-C (`husb311`) + USB role-switch / `usbdp_phy`~~ **done** — verify host, gadget, DP altmode on hardware.
8. ~~Charger (`sgm41542`) + gauge (`cw221X`) + `battery` node~~ **done** — verify on hardware (`upower`, `/sys/class/power_supply/`).
9. ~~SPI MCU joypad~~ **done** — driver backport + `&spi1` node.
10. ~~HDMI TX + HDMI audio~~ **done** — `&hdmi` / `&hdptxphy_hdmi` / VP0 / `hdmi_sound`. Reboot-mode, IMU when driver exists.

---

## Driver / config blockers (vendor tree)

| Feature | Edge dependency | In `linux-rk35xx-vendor` today? |
|---------|-----------------|----------------------------------|
| DSI panel | `rocknix,generic-dsi` (+ vendor backport) | **Yes** — `CONFIG_DRM_PANEL_ROCKNIX_GENERIC_DSI=y` |
| SPI joypad | `anbernic,spi-mcu-joypad` | **Yes** — `CONFIG_JOYSTICK_SPI_MCU_JOYPAD=y` (backport) |
| Charger | `sgm,sgm41542` | **Yes** — `CONFIG_CHARGER_SGM41542=y` (backport) |
| Fuel gauge | `cellwise,cw221X` | **Yes** — `CONFIG_BATTERY_CW221X=y` (backport) |
| Speaker amps | `awinic,aw87391` | **Yes** — `CONFIG_SND_SOC_AW87391=y` (backport) |
| WiFi | PCIe RTL8822CS | **Yes** — `CONFIG_RTW88_8822CS=y` |
| Type-C | `hynetek,husb311` | **Yes** — `CONFIG_TYPEC_HUSB311=y`, `CONFIG_USB_ROLE_SWITCH=y` |
| Touch | `syna,rmi4-i2c` | **Yes** — `CONFIG_RMI4_CORE/I2C/F12=y` |

---

## Related userspace (not DT, but coupled)

These Armbian BSP helpers assume edge-like DT/sysfs and may be inert until the matching nodes exist:

- `vita-jack-switch` — ALSA card / Headphone–Speaker switches (`rockchipes8388c` / `asound.state.anbernic-rg-vita-pro`)
- `vita-pad2key` — gpio-keys / joypad input
- `vita-screen` — DRM connector orientation
- `vita-offcharge` — power_supply + backlight
- `vita-typec-settle` — delay LightDM until USB-C partner present (cold-dock boot race)
- `vita-dock-displays` — post-login MST layout via `gdctl` (`/etc/default/vita-dock-displays`)

### Display output limits (RK3576)

Three VOP CRTCs (VP0, VP1, VP2). Only **three** simultaneous scanouts.

| Mode | Outputs | Notes |
|------|---------|--------|
| **dual** (default) | Panel + 2× USB-C DP | 2-lane HBR2 dock; ~1680×1050 + 1080p |
| **triple** | 3× USB-C DP | Panel off in layout; needs 3-port MST hub; stream2 (`dp2`) ≤1080p |
| **hdmi-combo** | HDMI + 2× USB-C DP | Panel off; HDMI uses VP0 (conflicts with MST stream on VP0 if panel on) |
| **SST cable** | 1× USB-C DP @ 4-lane | Direct cable; up to 1440p @ HBR2 |

Do not expect panel + HDMI + 2× USB-C at once (four outputs, three CRTCs). HDMI and MST stream1 both want VP0 when the panel is active.

---

*Generated for the first vendor DT iteration that produces a successful `BRANCH=vendor` image. Update this file as nodes are ported.*
