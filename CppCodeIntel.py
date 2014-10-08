import os
import sys
import re
import sublime
import sublime_plugin

if sys.platform != "win32" or sys.version_info[:2] >= (3, 0):
    dir_separate = '/' # Linux/Mac
else:
    dir_separate = '\\'

syntax_list = {
    "C++": True,
    "C": True,
    "Objective-C" : True,
    "Objective-C++": True
}
Debug = True
enabled = True

class CppCodeIntelEventListener(sublime_plugin.EventListener):
    def __init__(self):
        self.completions = [] # aqui vao todos os snippets, é regenerado a todo momento
        self.files = {} # aqui vao todos os arquivos
        # self.files['file.c']['word'] vao todas as palavras

    def isEnabled(self, view):
        syntax, _ = os.path.splitext(os.path.basename(view.settings().get('syntax')))
        if syntax_list.get(syntax) == None or not enabled:
            return False
        return syntax_list.get(syntax)

    def on_activated(self, view):
        if not view:
            return ;
        elif not self.isEnabled(view):
            return ;
        self.loadFile(view.file_name(), False, view.substr(sublime.Region(0, view.size())))

    def on_post_save_async(self, view):
        if not self.isEnabled(view):
            return ;
        self.loadFile(view.file_name(), True, view.substr(sublime.Region(0, view.size())))

    def on_query_completions(self, view, prefix, locations):
        if not self.isEnabled(view):
            return []
        return self.completions

    def loadFile(self, file, override_file=False, contents=None):
        if contents == None:
            f = open(file, 'r')
            contents = f.read()
            f.close()
        file_name = os.path.basename(file)
        dir_name = os.path.dirname(file)
        if not (self.files.get(file_name) == None or override_file):
            return ;
        if Debug: print("CppCodeIntel: loading file '"+file_name+"'")
        # reseta os snippets
        self.files[file_name] = {}
        #adicionando funcoes do tipo int func();
        matches = re.findall('(\w+)\**\s+(?:\w+\s+)*\**\s*([\w]+)\s*\(([^\)]*)\)', contents)
        for match in matches:
            if match[0] == 'return': # evitar confilitos como a linha 'return func(arg1, arg2);'
                continue
            elif match[1] == 'main': # nao usa snippet para main
                continue
            count = 1
            splited = match[2].split(', ')
            for j, string in enumerate(splited):
                try:
                    last_word = re.search('(\w+)+$', string).group()
                except:
                    continue
                splited[j] = '${'+str(count)+':'+last_word+'}'
                count += 1
            self.files[file_name][match[1]] = match[1]+'('+', '.join(splited)+')'
        #adicionando defines
        matches = re.findall('\#define\s+(\w+)', contents)
        for match in matches:
            self.files[file_name][match] = match
        #adicionando includes
        matches = re.findall('\#include\s*\"(.*)\"', contents)
        for include in matches:
            self.loadFile(dir_name+dir_separate+include)
        self.reloadCompletions()

    def reloadCompletions(self):
        self.completions = []
        funcs = {} # todas as funcoes definidas
        for file in self.files.values():
            for func in file:
                if funcs.get(func) == None:
                    self.completions += [(func, file[func])]
                    funcs[func] = True
