import argparse
import os
import re
import subprocess
import sys
data = ""
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
ADDR2LINE_64_PATH = os.path.join(CUR_DIR, "", "addr2line_breakpad.exe")

def addr2line(libpath, address, addr2line_path=None):
    if not addr2line_path:
        cmd = (ADDR2LINE_64_PATH, libpath, address)
    else:
        cmd = (addr2line_path, libpath, address)
    output = subprocess.check_output(cmd)
    if output:
        name = output.decode("utf-8").strip()
        name = name.replace("\n", " ")
        name = name.replace("\r", "")
        return " ".join(name.split()[1:])
    return None


def parse_unity_java_crash_dump_file(file_context):
    crash_info = {
        "backtrace": [],
        "abi": None,
        "modules": {},
        "miss": {},
    }
    p = re.compile(r'^at\s([^.]+)\.([^(]+)\([^)]+\)')
    line_number = 0
    for line in file_context.split("\n"):
        if "ABI" in line:
            m = re.search(r"ABI:\s?'(\w+)'", line)
            if m:
                crash_info['abi'] = m.group(1)
                # print("found abi", crash_info['abi'])

        if "BuildId" in line and "#" in line and ".so" in line:
            # TODO: #01 pc 00000000001d0cb4  /system/vendor/lib64/egl/libGLESv2_adreno.so (EsxVertexArrayObject::UpdateInternalVbos(EsxDrawDescriptor const*, unsigned int, EsxAttributeDesc const*)+1644)
            # print("BuildIdLine", line)
            ms = re.findall(r'#(\d+)\s+pc\s+([0-9a-fA-F]+)\s+([^\s]+)\s+(\([^\s].*)\s+\(BuildId:\s+([0-9a-fA-F]+)\)',
                            line)
            for m in ms:
                frame_index = int(m[0])
                address = m[1]
                libname = m[2]
                function_name = m[3]
                build_id = m[4]
                crash_info['modules'][libname] = build_id
                # print("found module", libname, build_id)
                function_name = function_name.strip('(')
                function_name = function_name.strip(')')

                crash_info['backtrace'].append({
                    "index": frame_index,
                    "libname": libname,
                    "address": address,
                    "function": function_name,
                })
                # print("found stack frame", libname, address, function_name)

        ms = re.findall(r'#(\d+)\s+pc\s+([0-9a-fA-F]+)\s+([^\s]+)\s+\(BuildId:\s+([0-9a-fA-F]+)\)', line)
        for m in ms:
            frame_index = int(m[0])
            address = m[1]
            libname = m[2]
            # function_name = m[3]
            build_id = m[3]
            crash_info['modules'][libname] = build_id
            # print("found module", libname, build_id)
            # function_name = parse_symbol(libname, build_id, address, crash_info['abi'])
            #  if function_name is None:
            #      crash_info['miss'][libname] = build_id
            crash_info['backtrace'].append({
                "index": frame_index,
                "libname": libname,
                "address": address,
                "function": "",
            })
                # print("found stack frame", libname, address, function_name)
        """
        if line.startswith("at "):
            m = p.search(line)
            if m:
                libname = m.group(1)
                if not libname.endswith(".so"):
                    libname += ".so"
                address = m.group(2)
                function_name = None
                symbol_file = find_symbol_file(g_symbols, libname, crash_info['modules'])
                if symbol_file:
                    function_name = addr2line(symbol_file, address, crash_info['abi'] == "arm64")
                else:
                    #if libname in crash_info['modules']:
                    crash_info['miss'][libname] = crash_info['modules'][libname]
                crash_info['backtrace'].append({
                    "libname": libname,
                    "address": address,
                    "function": function_name,
                })
        """
        line_number += 1
    return crash_info


def offset(frame, diff):
    hex_diff = diff.encode("utf-8").hex()
    hex1 = int(hex_diff, 16)
    hex2 = int(frame["address"], 16)
    frame["address"] = hex(hex1 + hex2)
    return frame


def parser(file, symbols, unity_diff=None, cpp_diff=None, addr2line_path=None,files_info=None):
    global data
    global data
    with open(file, "r",encoding="utf-8") as f:
        read = f.read()
    crash_info = parse_unity_java_crash_dump_file(read)
    # print(crash_info)
    for item in crash_info["backtrace"]:

        if os.path.basename(item['libname']) == "libunity.so" and unity_diff:
            item = offset(item, unity_diff)
        elif os.path.basename(item['libname']) == "libil2cpp.so" and cpp_diff:
            item = offset(item, cpp_diff)

        if item['libname'].endswith("so"):
            for sym in symbols:
                if os.path.basename(item['libname']) in os.path.basename(sym):
                    item["function"] = addr2line(sym, item["address"],addr2line_path)
        else:
            item["function"] = f"missing symbol file buildid[{crash_info['modules'][item['libname']]}]"

        data += "#%02d  %s %s %s %s \n" % (
            item['index'], os.path.basename(item['libname']), item['address'], hex(int(item['address'], 16)), item['function'])


def main():
    arges = argparse.ArgumentParser()
    arges.add_argument("-f", "--file", required=True, help="Unity java error file.")
    arges.add_argument("--symbols", nargs="+", required=True, help="Unity java error file.")
    arges.add_argument("-u", "--unity_diff", default=None, help="Unity_diff")
    arges.add_argument("-c", "--cpp_diff", default=None, help="cpp_diff")
    args = arges.parse_args()
    file = args.file
    unity_diff = args.unity_diff
    cpp_diff = args.cpp_diff
    symbols = args.symbols
    assert os.path.isfile(file), "传入文件路径异常"

    parser(file, symbols, unity_diff, cpp_diff)


if __name__ == "__main__":
    main()
