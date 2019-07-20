# -*- coding: utf-8 -*-

from unidecode import unidecode

# Intersecção de conjuntos
def interseccao(array1, array2):
    return [val for val in array1 if val in array2]

# União de conjuntos
def uniao(array1, array2):
    temp = array1 + array2
    return list(set(temp))

# Subtração de conjuntos
def subtracao(array1, array2):
    return list(set(array1) - set(array2))
        
def removeCaractersEspeciais(palavra):
    return palavra.lower().strip('!').replace('\n', '').replace('"', '').replace('\r', '').strip(';').strip(':')

def removeNonAscii(text):
    return unidecode(str(text))

def leaveOnlyCharsetInString(s, cset):
    for c in s:
        if c not in cset:
            s = s.replace(c, '')
    return s

def printDebug(msg):
    separator = '*************************************************************'
    print(separator)
    print(msg)
    print(separator)