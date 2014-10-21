import os
import sys
import re
from . import codefuncs
import sublime
import sublime_plugin

syntax_list = { #all allowed syntax
    "C++": True,
    "C": True,
    "Objective-C" : True,
    "Objective-C++": True
}
Debug = False #if true, see some comments on console
enabled = True #if true, this plugin will work, i guess... :)

class CppCodeIntelEventListener(sublime_plugin.EventListener):
    def __init__(self):
        self.completions = [] # aqui vao todos os snippets, é regenerado a todo momento # all snippets, it will be regenerate everytime
        self.files = {} # aqui vao todos os arquivos # all files
        # self.files['file.c']['func'] vao todas as palavras # self.files['file.c']['func'] == self.completions['func']

    def isEnabled(self, view):
        syntax, _ = os.path.splitext(os.path.basename(view.settings().get('syntax')))
        if syntax_list.get(syntax) == None or not enabled:
            return False
        elif view.file_name() == None:
            return False
        return syntax_list.get(syntax)

    def on_activated(self, view):
        if not view:
            return ;
        elif not self.isEnabled(view):
            return ;
        self.loadFile(view.file_name(), False, self.getContentsFromView(view))

    def on_post_save_async(self, view):
        if not self.isEnabled(view):
            return ;
        self.loadFile(view.file_name(), True, self.getContentsFromView(view))

    def on_close(self, view):
        if not self.isEnabled(view):
            return ;
        if Debug:
            print('CppCodeIntel: closed: '+os.path.basename(view.file_name()))
        self.removeFile(view.file_name())
        self.reloadCompletions()

    def on_query_completions(self, view, prefix, locations):
        if not self.isEnabled(view):
            return []
        return self.completions

    def removeFile(self, file_path):
        '''
        this function is called when a file is removed, 
        this file will be removed from self.files too
        '''
        file_name = os.path.basename(file_path)
        path = os.path.dirname(file_path)
        if self.files.get(file_name) != None:
            if Debug:
                print('CppCodeIntel: removing file: '+file_name)
            del self.files[file_name]
            if not os.path.exists(file):
                return ; # file not exists
            with open(os.path.join(path, file_name), "r") as file:
                contents = file.read()
            includes = getIncludesFromContent(contents)
            for include in includes:
                self.removeFile(os.path.join(path, include))

    def loadFile(self, file_path, override_file=False, file_contents=None):
        '''
        this function will load a file in self.files
        '''
        if file_contents == None:
            if not os.path.exists(file_path):
                return ; # file not exists
            with open(file_path, 'r') as file:
                file_contents = file.read()
        file_name = os.path.basename(file_path)
        dir_name = os.path.dirname(file_path)
        settings = sublime.load_settings("cppcodeintel.sublime-settings")
        self.show_only_last_word = settings.get("show_only_last_word", False)
        if not (self.files.get(file_name) == None or override_file):
            return ;
        if Debug: print("CppCodeIntel: loading file '"+file_name+"'")
        #cleaning the file
        file_contents = codefuncs.cleanCode(file_contents)
        # reseta os snippets do arquivo file_name # clear all snippets of file_name
        self.files[file_name] = {}
        #adding important_words
        important_words = getImportantWordsFromContent(file_contents)
        for word in important_words:
            self.files[file_name][word] = word
        #adicionando funcoes do tipo int func(parameters) # adding functions like int func(parameters)
        funcs = getFunctionsFromContent(file_contents)
        for (type, func_name, parameters) in funcs:
            if type == 'return': # evitar confilitos como a linha 'return func(arg1, arg2);'
                continue
            elif func_name == 'main': # nao adiciona main aos snippets
                continue
            elif func_name == 'if': # nao adiciona if aos snippets
                continue
            count = 1
            params_splited = parameters.split(', ')
            for i, arg in enumerate(params_splited):
                if arg == '':
                    continue
                elif self.show_only_last_word == False:
                    snippet_word = arg
                else:
                    try:
                        snippet_word = re.search('\w+(?:\[(?:\w+)?\])*$', arg).group()
                    except:
                        snippet_word = arg
                params_splited[i] = '${'+str(count)+':'+snippet_word+'}'
                count += 1
            self.files[file_name][func_name] = func_name+'('+', '.join(params_splited)+')'
        #adicionando includes # adding files in #include "file"
        includes = getIncludesFromContent(file_contents)
        for include in includes:
            self.loadFile(os.path.join(dir_name, include))
        self.reloadCompletions()

    def reloadCompletions(self):
        '''
        this function makes self.completions
        '''
        if Debug:
            print('CppCodeIntel: reloading completions')
            print('\tfiles to process: '+' '.join(self.files.keys()))
        del self.completions[:]
        funcs = {} # todas as funcoes definidas
        for file in self.files.values():
            for func in file:
                if funcs.get(func) == None:
                    self.completions += [(func, file[func])]
                    funcs[func] = True

    def getContentsFromView(self, view):
        '''
        return the contents inside the view
        '''
        return view.substr(sublime.Region(0, view.size()))

def getIncludesFromContent(file_contents):
    '''
    return all files that is mettioned in #include "file.c"
    '''
    return re.compile('#\s*include\s*\"([^\"]+)\"').findall(file_contents)

def getFunctionsFromContent(file_contents):
    '''
    return all functions like (type, func_name, parameters)
    '''
    return re.compile('(\w+)\**\s+(?:\w+\s+)*\**\s*([\w]+)\s*\(([^\)]*)\)').findall(file_contents);

def getImportantWordsFromContent(file_contents):
    '''
    return important words
    '''
    #adicionando palavras, tipo #define word # adding words like #define word
    result = re.compile('\#\s*define\s+(\w+)').findall(file_contents)
    #adicionando palavras do tipo typedef word snippet; #adding words like typedef word
    result += re.compile('typedef(?:\s+\w+)+\s+(\w+)\s*;').findall(file_contents)
    #adicionando palavras do tipo typedef struct {} word; #adding words like typedef struct {} word;
    # result += re.compile('typedef [^\}]*\} ?(\w+);').findall(file_contents)
    return result