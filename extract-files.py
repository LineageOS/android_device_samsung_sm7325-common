#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2025 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from extract_utils.fixups_blob import (
    BlobFixupCtx,
    File,
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)
from extract_utils.tools import (
    llvm_objdump_path,
)
from extract_utils.utils import (
    run_cmd,
)

namespace_imports = [
    'device/samsung/sm7325-common',
    'hardware/qcom-caf/sm8350',
    'hardware/qcom-caf/wlan',
    'hardware/samsung',
    'vendor/qcom/opensource/dataservices',
    'vendor/qcom/opensource/display',
]


def blob_fixup_ril_smsc(
    ctx: BlobFixupCtx,
    file: File,
    file_path: str,
    *args,
    **kwargs,
):
    func_offset = None
    func_size = None

    output = run_cmd([llvm_objdump_path, '-T', file_path])
    for line in output.splitlines():
        if 'OnGetSmscAddressDone' in line:
            parts = line.split()
            if len(parts) >= 5:
                func_offset = int(parts[0], 16)
                func_size = int(parts[-2], 16)
                break

    if func_offset is None or func_size is None:
        return

    with open(file_path, 'rb+') as f:
        f.seek(func_offset)
        func_data = f.read(func_size)
        anchor_pos = func_data.find(b'\x82\x0c\x80\x52')

        if anchor_pos != -1:
            for i in range(4, 32, 4):
                if anchor_pos + i + 4 > func_size:
                    break

                instr = func_data[anchor_pos + i : anchor_pos + i + 4]

                if (instr[3] == 0xaa and instr[1] == 0x03 and (instr[0] & 0x1f) == 3):
                    patch_offset = func_offset + anchor_pos + i
                    f.seek(patch_offset)
                    f.write(b'\x03\x00\x80\xd2') # mov x3, #0
                    break


lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
}

blob_fixups: blob_fixups_user_type = {
    'vendor/lib64/libsec-ril.so': blob_fixup()
        .binary_regex_replace(b'ril.dds.call.ongoing', b'vendor.calls.slot_id')
        .call(blob_fixup_ril_smsc),
    ('vendor/lib64/hw/gatekeeper.mdfpp.so', 'vendor/lib64/libkeymaster_helper.so', 'vendor/lib64/libskeymaster4device.so'): blob_fixup()
        .replace_needed('libcrypto.so', 'libcrypto-v33.so'),
    ('vendor/lib/libdpps.so', 'vendor/lib64/libdpps.so', 'vendor/lib/libsnapdragoncolor-manager.so', 'vendor/lib64/libsnapdragoncolor-manager.so'): blob_fixup()
        .replace_needed('libtinyxml2.so', 'libtinyxml2-v34.so'),
    ('vendor/lib/libwvhidl.so', 'vendor/lib/mediadrm/libwvdrmengine.so'): blob_fixup()
        .add_needed('libcrypto_shim.so'),
    ('vendor/lib/unihal_main@2.15.so', 'vendor/lib64/unihal_main@2.15.so'): blob_fixup()
        .add_needed('libui_shim.so'),
}  # fmt: skip

module = ExtractUtilsModule(
    'sm7325-common',
    'samsung',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
