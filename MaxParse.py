import re
import Logger

def parse(file, *args, **kwargs):

    lines = file.readlines()

    for index, line in enumerate(lines):
        instruction_match = re.search(r'mp!\([\w-]*\??[\w-]*\)', line)
        while instruction_match:
            result = parse_instruction(instruction_match, line, *args, **kwargs)
            span = instruction_match.span()
            line = line[:span[0]] + result + line[span[1]:]

            instruction_match = re.search(r'mp!\([\w-]*\??[\w-]*\)', line)
        lines[index] = line

    return lines

def parse_instruction(match, line, *args, **kwargs):
    string = line[match.span()[0]:match.span()[1]]
    string = string[4:-1]
    if '?' in string:
        match_string, default_string = string.split('?')

        #See if instruction is an index
        try:
            index = int(match_string)
            try:
                return args[index]
            except IndexError:
                return default_string
        #If it isn't an index treat it like a key word
        except ValueError:
            try:
                return kwargs[match_string]
            except KeyError:
                return default_string
    else:
        try:
            index = int(string)
            try:
                return args[index]
            except IndexError:
                return ''
        #If it isn't an index treat it like a key word
        except ValueError:
            try:
                return kwargs[string]
            except KeyError:
                return ''
    return ''
