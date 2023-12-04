import re
import os
import sys


def get_begin(file_path):
    crash_start = "--------- beginning of crash"

    with open(file_path, 'r', encoding="utf-8") as file:
        lines = file.readlines()

    line_numbers = [i + 1 for i, line in enumerate(lines) if line.startswith(crash_start)]
    return line_numbers[0]


def get_end(file_path):
    pattern = r"^.*DEBUG.*(\#(\d)*)+.*$"
    match_lines = []

    with open(file_path, 'r', encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            matches = re.finditer(pattern, line)
            for match in matches:
                match_lines.append(line_number)
    # print(match_lines)
    if len(match_lines) > 0:
        return match_lines[-1]
    print("未发现backtrace堆栈")
    return 0


def extract_lines(file_path, start_line, end_line,output_path):
    lines = []
    with open(file_path, 'r', encoding="utf-8") as file:
        lines = file.readlines()

    extracted_lines = lines[start_line - 1:end_line]
    # print("\r".join(extracted_lines))
    with open(output_path, 'a+') as output_file:
        output_file.writelines(extracted_lines)

def crash_begin(file_path,output_path):
    with open(file_path, 'r',encoding="utf-8") as file:
        file_path = file.read()

    ndk_crash_begin = r'.*Crasheye NDK Crash Begin.*[\r\n].*[\r\n].*'
    str = re.findall(ndk_crash_begin, file_path)
    if str != []:
        header = "\r".join(str) + "\n"
        # print(header)
        with open(output_path, 'w') as output_file:
            output_file.writelines(header)
            output_file.write('\n')

file_path = sys.argv[1]
output = os.path.basename(file_path).rsplit(".")[0]+ "+backtrace.txt"
crash_begin(file_path,output)
if get_end(file_path) != 0:
    extract_lines(file_path, get_begin(file_path), get_end(file_path), output)


