from .claude_code import parse as parse_messages


def parse(filename, text):
    return parse_messages(filename, text, 'workbuddy')
