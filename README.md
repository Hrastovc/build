<h2 align="center">
  <a href=#><img src="https://raw.githubusercontent.com/armbian/.github/master/profile/logosmall.png" alt="Armbian logo"></a>
  <br><br>
</h2>

# Armbian Linux Build Framework

## Purpose of This Repository

The **Armbian Linux build framework** creates customizable OS images based on **Debian** or **Ubuntu** for **single-board computers (SBCs)** and embedded devices. It builds a complete Linux system — kernel, bootloader, and root filesystem — giving you control over versions, configuration, firmware, device trees, and system optimizations.

The framework supports **native**, **cross**, and **containerized** builds for multiple architectures (`x86_64`, `aarch64`, `armhf`, `riscv64`) and is suitable for development, testing, production, or automation.

> **Looking for prebuilt images?** Use [Armbian Imager](https://github.com/armbian/imager/releases) — the easiest way to download and flash Armbian to your SD card or USB drive. Available for Linux, macOS, and Windows.

## Quick Start

```bash
git clone https://github.com/armbian/build
cd build
./compile.sh
```

<a href="#quick-start"><img src=".github/README.gif" alt="Build demonstration" width="100%"></a>

## Build Host Requirements

### Hardware
- **RAM:** ≥8 GB (less with `KERNEL_BTF=no`)
- **Disk:** ~50 GB free space
- **Architecture:** `x86_64`, `aarch64`, or `riscv64`

### Operating System
- **Native builds:** Armbian / Debian 13 (Trixie)
- **Containerized:** any Docker-capable Linux
- **Windows:** WSL2 with Armbian / Debian 13 (Trixie)

### Software
- Superuser privileges (`sudo` or root)
- Up-to-date system (outdated Docker or other tools can cause failures)

## Built With

- **Bash** — the build framework itself (`compile.sh`, `lib/`, `extensions/`, board/family configs)
- **Python** — helper tooling used by the framework
- **Make / Kbuild** — device-tree overlay Makefiles under `patch/kernel/**/overlay/`
- **YAML** — GitHub Actions workflows and repository configuration
- **Patches, defconfigs and device trees** — kernel and U-Boot customizations under `patch/`, `config/kernel/`, and related directories

## Repository Layout

| Path | Description |
|:--|:--|
| `compile.sh` | Main entrypoint; bootstraps the framework and dispatches the CLI |
| `lib/` | Core Bash library implementing the build framework |
| `extensions/` | Optional build-time extensions |
| `config/` | Build configuration: boards, families/sources, distributions, kernel configs, bootenv, bootscripts, etc. |
| `config/boards/` | Per-board configuration files (`*.conf`, `*.csc`, `*.eos`, `*.tvb`, `*.wip`) |
| `config/sources/` | Family / SoC definitions |
| `config/distributions/` | Supported Debian and Ubuntu userspace releases |
| `patch/` | Kernel and U-Boot patches, device trees and overlays |
| `packages/` | Kernel packaging scripts, BSP files (`bsp-cli`, `bsp-desktop`) and related packaging bits |
| `tools/` | Small helper tools (e.g. `mk_format_patch`, `unifying_configs`) |
| `.github/` | Issue/PR templates, labels, CODEOWNERS and GitHub Actions workflows |
| `action.yml` | Composite GitHub Action for building Armbian images / kernels in workflows |

### Board configuration extensions

Board configs live in `config/boards/` and use their file extension to signal support status:

| Extension | Status |
|:--|:--|
| `.conf` | Supported |
| `.csc`  | Community maintained / unstable |
| `.eos`  | End of life |
| `.tvb`  | TV box |
| `.wip`  | Work in progress |

See [`config/boards/README.md`](config/boards/README.md) for the full list of board options (e.g. `BOARD_NAME`, `BOARDFAMILY`, `BOOTCONFIG`, `KERNEL_TARGET`, `SERIALCON`, `DEFAULT_OVERLAYS`, …).

## Using Armbian as a GitHub Action

This repository also ships a composite GitHub Action (`action.yml`, "Rebuild Armbian") that can build an image or a kernel from a workflow. Selected inputs:

| Input | Purpose |
|:--|:--|
| `armbian_target` | `image` or `kernel` (default: `kernel`) |
| `armbian_board` | Target board (default: `uefi-x86`) |
| `armbian_branch` | Framework branch (default: `main`) |
| `armbian_kernel_branch` | Kernel branch, e.g. `current`, `edge`, `legacy` |
| `armbian_release` | Userspace release (default: `noble`) |
| `armbian_ui` | `minimal`, `server`, or a desktop environment |
| `armbian_compress` | Output compression, e.g. `sha,img,xz` |
| `armbian_extensions` | Space-separated list of build extensions to enable |
| `armbian_pgp_key` / `armbian_pgp_password` | Optional signing of build artifacts |

See `action.yml` for the full set of inputs and defaults.

## Continuous Integration

An always-current overview of this repository's CI status and workflow runs is available at:

👉 [actions.armbian.com — build](https://actions.armbian.com/?repo=build)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on reporting issues, working on existing tickets, preparing patches and submitting pull requests. Credits for contributors are collected in [CREDITS.md](CREDITS.md).

## Resources

- **[Documentation](https://docs.armbian.com/Developer-Guide_Overview/)** — comprehensive guides for building, configuring, and customizing
- **[Website](https://www.armbian.com)** — news, features, and board information
- **[Blog](https://blog.armbian.com)** — development updates and technical articles
- **[Forums](https://forum.armbian.com)** — community support and discussions

## Support

### Community Forums
Get help from users and contributors on troubleshooting, configuration, and development.
👉 [forum.armbian.com](https://forum.armbian.com)

### Real-time Chat
Join discussions with developers and community members on IRC or Discord.
👉 [Community Chat](https://docs.armbian.com/Community_IRC/)

### Paid Consultation
For commercial projects, guaranteed response times, or advanced needs, paid support is available from Armbian maintainers.
👉 [Contact us](https://www.armbian.com/contact)

## Contributors

Thank you to everyone who has contributed to Armbian!

<a href="https://github.com/armbian/build/graphs/contributors">
  <img alt="Contributors" src="https://contrib.rocks/image?repo=armbian/build" />
</a>

## Armbian Partners

Our [partnership program](https://forum.armbian.com/subscriptions) supports Armbian's development and community. Learn more about [our Partners](https://armbian.com/partners).

## License

This project is licensed under the **GNU General Public License v2.0**. See [LICENSE](LICENSE) for details.
