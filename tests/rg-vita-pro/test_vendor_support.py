import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
BSP = ROOT / 'config/optional/boards/anbernic-rg-vita-pro/_packages/bsp-cli'


def helper(name):
    loader = importlib.machinery.SourceFileLoader(name, str(BSP / 'usr/bin' / name))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader))
    loader.exec_module(module)
    return module


def edid(serial=1):
    data = bytearray(128)
    data[:12] = bytes.fromhex('00ffffffffffff0010ac42f0')
    data[12:16] = serial.to_bytes(4, 'little')
    data[18:20] = bytes([1, 3])
    data[54:72] = bytes.fromhex('21399030621a274068b03600d9281100001c')
    data[127] = -sum(data[:127]) & 255
    return bytes(data)


def test_custom_profile_preserves_identity_and_fits_two_lanes():
    profile = helper('vita-dock-profile').p2213_profile(edid())
    assert profile[8:54] == edid()[8:54]
    assert sum(profile) % 256 == 0
    clock = int.from_bytes(profile[54:56], 'little') * 10
    assert clock == 125000
    pbn = (clock * 24 * 64 * 1006 + 432000000 - 1) // 432000000
    assert pbn == 448
    assert 29 + 2 * ((pbn + 29) // 30) == 59


def test_forced_profile_matches_only_the_captured_monitor(tmp_path):
    watch = helper('vita-dock-edid-watch')
    profile = helper('vita-dock-profile').p2213_profile(edid())
    path = tmp_path / 'monitor.force.bin'
    path.write_bytes(profile)
    profiles = watch.load_profiles(tmp_path)
    assert watch.replacement(edid(), ['1680x1050'], profiles) == profile
    assert watch.replacement(edid(2), ['1680x1050'], profiles) is None
    assert watch.replacement(profile, ['1680x1050'], profiles) is None
    path.rename(tmp_path / 'monitor.bin')
    assert watch.replacement(edid(), ['1680x1050'], watch.load_profiles(tmp_path)) is None


def test_invalid_and_unidentified_profiles_are_rejected(tmp_path):
    tool = helper('vita-dock-profile')
    for data in [edid()[:-1], bytes(128), edid(0)]:
        with pytest.raises(ValueError):
            tool.p2213_profile(data)
    (tmp_path / 'invalid.force.bin').write_bytes(edid(0))
    assert helper('vita-dock-edid-watch').load_profiles(tmp_path) == {}


def test_p2p_addresses_are_stable_local_and_device_specific():
    address = helper('vita-p2p-address').address
    first = address('1' * 32, 'p2p0')
    assert first == address('1' * 32, 'p2p0')
    assert first != address('2' * 32, 'p2p0')
    assert first != address('1' * 32, 'p2p1')
    assert int(first[:2], 16) & 3 == 2
    with pytest.raises(ValueError):
        address('', 'p2p0')
    with pytest.raises(ValueError):
        address('1' * 32, 'wlan0')


@pytest.mark.parametrize('branch', ['vendor', 'edge'])
@pytest.mark.parametrize('configured', [False, True])
def test_bsp_branch_isolation_and_image_inputs(tmp_path, branch, configured):
    package = tmp_path / 'package'
    image = tmp_path / 'image'
    private = tmp_path / 'inputs'
    shutil.copytree(BSP, package)
    shutil.copytree(BSP, image)
    (package / 'DEBIAN').mkdir()
    (package / 'DEBIAN/conffiles').write_text(
        '/etc/modprobe.d/vita-touch-defer.conf\n/etc/default/vita-offcharge\n')
    (private / 'vita-dock-edid').mkdir(parents=True)
    profile = helper('vita-dock-profile').p2213_profile(edid())
    if configured:
        (private / 'vita-dock-edid/monitor.force.bin').write_bytes(profile)
        (private / 'vita-dock-displays.conf').write_text('DISABLE=0\n')
    command = '''
set -eu
display_alert() { :; }
source "$1"
BRANCH=$2 destination=$3 SDCARD=$4 USERPATCHES_PATH=$5 BOARD=test
post_family_tweaks_bsp__anbernic_rg_vita_pro_vendor
post_family_tweaks__anbernic_rg_vita_pro_helpers
add_packages_to_image() { printf '%s\n' "$@" > "$SDCARD/packages.txt"; }
BUILD_DESKTOP=yes DESKTOP_ENVIRONMENT=gnome
user_config__anbernic_rg_vita_pro_dock_packages
'''
    subprocess.run(['bash', '-c', command, 'test',
                    str(ROOT / 'config/boards/anbernic-rg-vita-pro.conf'),
                    branch, str(package), str(image), str(private)], check=True)
    unit = package / 'etc/systemd/system/multi-user.target.wants/vita-dock-edid.service'
    if branch == 'vendor':
        assert unit.is_symlink()
        assert (package / 'etc/modprobe.d/vita-touch-defer.conf').exists()
        assert (image / 'etc/vita-dock-displays.conf').exists() == configured
        if configured:
            assert (image / 'etc/vita-dock-edid/monitor.force.bin').read_bytes() == profile
            assert (image / 'etc/vita-dock-displays.conf').read_text() == 'DISABLE=0\n'
        assert 'mutter-common-bin' in (image / 'packages.txt').read_text()
    else:
        assert not unit.is_symlink()
        assert not (package / 'etc/modprobe.d/vita-touch-defer.conf').exists()
        assert not (package / 'usr/bin/vita-dock-displays').exists()
        assert not (image / 'etc/vita-dock-displays.conf').exists()
        assert 'vita-touch-defer' not in (package / 'DEBIAN/conffiles').read_text()
        assert not (image / 'packages.txt').exists()


@pytest.mark.parametrize('verify_failure', [False, True])
def test_layout_uses_preferred_modes_without_changing_displays(tmp_path, verify_failure):
    binaries = tmp_path / 'bin'
    binaries.mkdir()
    log = tmp_path / 'calls.jsonl'
    script = binaries / 'gdctl'
    script.write_text('''#!/usr/bin/python3
import json, os, sys
with open(os.environ['CALL_LOG'], 'a') as output:
    output.write(json.dumps(sys.argv[1:]) + '\\n')
sys.exit(int('--verify' in sys.argv and os.environ['VERIFY_FAILURE'] == '1'))
''')
    script.chmod(0o755)
    (binaries / 'sleep').symlink_to('/usr/bin/true')
    stub = tmp_path / 'gi/repository'
    stub.mkdir(parents=True)
    (stub.parent / '__init__.py').write_text('')
    (stub / '__init__.py').write_text('''import json, os
class Gio:
    class BusType: SESSION = 0
    class DBusProxyFlags: NONE = 0
    class DBusCallFlags: NO_AUTO_START = 0
    class DBusProxy:
        @staticmethod
        def new_for_bus_sync(*args):
            return Gio.DBusProxy()
        def call_sync(self, *args):
            return self
        def unpack(self):
            return json.loads(os.environ['MONITOR_STATE'])
''')
    def monitor(name, width, height, mode):
        return [[name, 'TEST', 'TEST', '1'],
                [[mode, width, height, 60.0, 1.0, [1.0], {'is-preferred': True}]], {}]
    state = [1, [monitor('DSI-1', 800, 600, '800x600@60.000'),
                 monitor('DP-2', 2560, 1440, '2560x1440@60.000'),
                 monitor('DP-3', 1920, 1080, '1920x1080@60.000'),
                 monitor('DP-4', 1920, 1080, '1920x1080@60.000')], [], {}]
    env = os.environ | {
        'PATH': f'{binaries}:{os.environ["PATH"]}', 'PYTHONPATH': str(tmp_path),
        'HOME': str(tmp_path), 'XDG_RUNTIME_DIR': str(tmp_path),
        'XDG_SESSION_TYPE': 'wayland', 'VITA_DOCK_DISABLE': '0',
        'VITA_DOCK_REQUIRE_DOCK': '0', 'VITA_DOCK_MODE': 'triple',
        'VITA_DOCK_TRIPLE_HI': 'auto', 'VITA_DOCK_TRIPLE_MID': 'auto',
        'VITA_DOCK_TRIPLE_LO': 'auto', 'VITA_DOCK_PANEL_MODE': 'auto',
        'VITA_DOCK_PANEL_SCALE': 'auto', 'CALL_LOG': str(log),
        'VERIFY_FAILURE': str(int(verify_failure)), 'MONITOR_STATE': json.dumps(state),
    }
    result = subprocess.run([str(BSP / 'usr/bin/vita-dock-displays'), '--verify-only'], env=env)
    assert bool(result.returncode) == verify_failure
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    configurations = [call for call in calls if call[0] == 'set']
    assert len(configurations) == 1
    assert '--verify' in configurations[0]
    assert '2560x1440@60.000' in configurations[0]
    assert configurations[0].count('1920x1080@60.000') == 2
