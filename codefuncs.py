import re

def cleanCode(file_contents):
    '''
    remove all comments and non important code
    '''
    #removing comments
    file_contents = re.sub('//[^\n]*\n?', '\n', file_contents)
    file_contents = re.sub('\/\*.*?\*\/', '', file_contents)
    # removing {|} inside in strings
    file_contents = re.sub('".*(\{|\}).*"', '', file_contents)
    file_contents = re.sub("'.*(\{|\}).*'", '', file_contents)
    #removing {}
    result = ''
    opened_brackets = 0
    for char in file_contents:
        if char == '{':
            opened_brackets+=1
        elif char == '}':
            opened_brackets-=1
        elif opened_brackets == 0:
            result += char
    return result