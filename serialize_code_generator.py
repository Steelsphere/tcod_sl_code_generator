import sys
import os
import CppHeaderParser

headers = []
classes = []

type_only = None
type_only_others = []


class CPPAttribute:
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def __repr__(self):
        return str((self.name, self.type))


class CPPClass:

    def __init__(self):
        self.name = ""
        self.parent = None
        self.file = ""
        self.attrs = []

    def __repr__(self):
        return str((self.name, self.file, self.attrs))

    def generate_code(self):
        output_string = f'void {self.name}::serialize(TCODZip* zip) {{\n'

        # Serialize
        if self.parent is not None:
            output_string += f'\t{self.parent}::serialize(zip);\n'

        for i in self.attrs:
            real_type = i.type

            if i.type.split()[0] == 'static':
                i.type = i.type.split()[1]

            if i.type == 'int' or i.type == 'unsigned int' or i.type == 'long' or i.type == 'unsigned long'\
                    or i.type == 'bool' or i.type == 'long long' or i.type == 'unsigned long long':
                output_string += f'\tzip->putInt({i.name});\n'
            elif i.type == 'char' or i.type == 'unsigned char':
                output_string += f'\tzip->putChar({i.name});\n'
            elif i.type == 'const char*':
                output_string += f'\tzip->putString({i.name});\n'
            elif i.type == 'std::string':
                output_string += f'\tzip->putString({i.name}.c_str());\n'
            elif i.type == 'float' or i.type == 'double':
                output_string += f'\tzip->putFloat({i.name});\n'
            elif i.type == 'TCODColor':
                output_string += f'\tzip->putColor(&{i.name});\n'
            elif i.type == 'TCODConsole':
                output_string += f'\tzip->putConsole({i.name});\n'
            else:
                output_string += f'\t{i.name}.serialize(zip); // {real_type}\n'
        output_string += '}\n\n'

        output_string += f'void {self.name}::deserialize(TCODZip* zip) {{\n'

        # Deserialize
        if self.parent is not None:
            output_string += f'\t{self.parent}::deserialize(zip);\n'

        for i in self.attrs:
            real_type = i.type

            if i.type.split()[0] == 'static':
                i.type = i.type.split()[1]

            if i.type == 'int' or i.type == 'unsigned int' or i.type == 'long' or i.type == 'unsigned long'\
                    or i.type == 'bool':
                output_string += f'\t{i.name} = zip->getInt();\n'
            elif i.type == 'char' or i.type == 'unsigned char':
                output_string += f'\t{i.name} = zip->getChar();\n'
            elif i.type == 'const char*':
                output_string += f'\t{i.name} = zip->getString();\n'
            elif i.type == 'std::string':
                output_string += f'\t{i.name} = zip->getString();\n'
            elif i.type == 'float' or i.type == 'double':
                output_string += f'\t{i.name} = zip->getFloat();\n'
            elif i.type == 'TCODColor':
                output_string += f'\t{i.name} = zip->getColor();\n'
            elif i.type == 'TCODConsole':
                output_string += f'\t{i.name} = zip->getConsole();\n'
            else:
                output_string += f'\t{i.name}.deserialize(zip); // {real_type}\n'
        output_string += '}\n\n'

        return output_string


def parse_file(file):
    parser = CppHeaderParser.CppHeader(file)
    print(len(parser.classes), file)
    for i in parser.classes_order:
        obj = CPPClass()
        obj.name = i['name']
        obj.file = os.fsdecode(file)
        if len(i['inherits']) != 0:
            obj.parent = i['inherits'][0]['class']
        for access in ['public', 'protected', 'private']:
            for j in i['properties'][access]:
                if not (j['pointer'] and j['type'].split()[0] == 'const'):
                    if j['pointer'] == 1:
                        continue
                    if j['type'].split()[0] == 'const':
                        continue
                obj.attrs.append(CPPAttribute(j['name'], j['type']))
        classes.append(obj)


def fill_type_only_others():
    times = 1
    while times > 0:
        times = 0
        for c in classes:
            if (c.parent == type_only or c.parent in type_only_others) and c.name not in type_only_others:
                type_only_others.append(c.name)
                if times == 0:
                    times = 1


def add_helper_function():
    string = ''
    string += 'template <typename T>\n'
    string += f'static {type_only}* create_{type_only.lower()}_instance() {{ return new T; }}\n\n'
    string += f'std::map<std::string, {type_only}*(*)()> type_map = {{\n'
    for c in classes:
        if c.name == type_only or c.parent == type_only \
                or c.parent in type_only_others or c.name in type_only_others:
            string += f'\t{{ typeid({c.name}).name(), create_{type_only.lower()}_instance<{c.name}> }},\n'
    string += '};\n'
    return string

for file in os.listdir(os.fsdecode(sys.argv[1])):
    filename = os.fsdecode(file)
    if filename.endswith('.h'):
        headers.append(filename)

os.chdir(sys.argv[1])

if len(sys.argv) > 2:
    type_only = sys.argv[2]

for h in headers:
    parse_file(h)

final_output = ""

fill_type_only_others()

for c in classes:
    if type_only is not None:
        if c.name == type_only or c.parent == type_only \
                or c.parent in type_only_others or c.name in type_only_others:
            final_output += f'// {c.file} - {c.name} - inherits {c.parent}\n'
            final_output += c.generate_code()
    else:
        final_output += f'// {c.file} - {c.name} - inherits {c.parent}\n'
        final_output += c.generate_code()

if type_only is not None:
    final_output += '// Helps deserialize derived types\n\n'
    final_output += add_helper_function()


os.chdir(os.path.dirname(os.path.realpath(__file__)))

with open('serializer_output.cpp', 'w') as f:
    f.write(final_output)

print('Done')

