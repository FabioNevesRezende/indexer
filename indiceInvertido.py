# -*- coding: utf-8 -*-
import json, math, traceback, magic, re, pdftotext
mime = magic.Magic(mime=True)
from utils import *

'''
    A classe tupla representará a lista de documentos e quantidades
    exemplo:
    { 'documento1': 3, 'documento2': 4 }
'''
class tupla(json.JSONEncoder):
    def __init__(self):
        self.tupla = {}
    def __init__(self, doc, qtdade):
        self.tupla = { doc: qtdade }

    def default(self, object):
        if isinstance(object, tupla):
            return object.__dict__
        else:
            return json.JSONEncoder.default(self, object)

    def documentoNaTupla(self, d):
        for chave in self.tupla:
            if d == chave:
                return True
        return False

    def addItemTupla(self, documento, quantidade):
        self.tupla[documento] = quantidade

    def qtdadeNoDocumento(self, documento): # este é o fij da fórmula
        return self.tupla[documento]

    def atualizaQtdade(self, documento, quantidade):
        self.tupla[documento] = quantidade

    def incrementa(self, documento):
        self.tupla[documento] += 1
        
'''
    A classe IndiceInvertido representará o próprio índice e cada palavra referenciará uma tupla (da classe anterior)
    exemplo:
    { 'palavra1': { 'documento1': 3, 'documento2': 4 }}
    { 'palavra2': { 'documento2': 1, 'documento3': 7 }}
'''
class IndiceInvertido(json.JSONEncoder):
    def __init__(self, base, stop_words, jsonPath=''):
        try:
            self.tuplas = {}
            self.stop_words = stop_words
            self.jsonPath = jsonPath
            self.base = base

            self.nroDocumentos = self.calculateNumDocs()

            if self.jsonPath and len(self.jsonPath) > 0:
                self.fromJsonStr()
        
            with open(self.base, 'r') as arq:
                for d in arq.readlines():
                    d = d.strip('\n')
                    mimeType = magic.from_file(d, mime=True)
                    if mimeType == 'text/plain':
                        with open(d.strip('\n'), 'r') as doc:
                            for linha in doc.readlines():
                                self.parsearFraseInsertIndice(linha, d)
                    elif mimeType == 'application/pdf':
                        with open(d, "rb") as f:
                            pdf = pdftotext.PDF(f)
                            for page in pdf:
                                self.parsearFraseInsertIndice(page, d)
                                
                        print('Finalizada leitura do pdf ' + d)

        except Exception as e:
            print(str(e))
            traceback.print_exc() 
            exit(1)

    def parsearFraseInsertIndice(self, frase, doc):
        palavrasDaFrase = re.split('[\.\? ,!]', frase) # cria vetor de strings com cada palavra separada pelos símbolos "." "?" "," e " "
        allowedChars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZçÇáÁàÀãÃâÂéÉêÊíÍóÓõÕôÔúÚ'
        for palavra in palavrasDaFrase:
            if palavra != '' and palavra != '\n' and palavra.lower() not in self.stop_words:
                self.addPalavra(removeCaractersEspeciais(leaveOnlyCharsetInString(palavra,allowedChars)), doc)

    def calculateNumDocs(self):
        num = 0
        try:
            with open(self.base, 'r') as arq:
                num = len(arq.readlines())
        except FileNotFoundError as e:
            pass

        printDebug('Num docs calculados' + str(num))
        return num

    def default(self, object):
        if isinstance(object, IndiceInvertido):
            return object.__dict__
        else:
            return json.JSONEncoder.default(self, object)

    def addPalavra(self, p, d):
        try:
            if self.tuplas[p]:
                for documento in self.tuplas[p].tupla:
                    if d == documento:
                        self.tuplas[p].incrementa(documento)
                        return
                self.tuplas[p].addItemTupla(d, 1)
        except KeyError as e:
            self.tuplas[p] = tupla(d,1)

    def printaIndiceInvertido(self):
        print('Estado atual do índice invertido:')
        for chave in self.tuplas:
            print('Palavra: ' + chave)
            for documento in self.tuplas[chave].tupla:
                print('doc: ' + str(documento) + ' qtdade: ' + str(self.tuplas[chave].tupla[documento]))
               
    def toJsonStr(self):
        finalJsonStr = ''
        finalJsonStr += '{'
        chaves = len(self.tuplas)
        countOuter = 0
        for chave in self.tuplas:
            tpls = len(self.tuplas[chave].tupla)
            countInner = 0
            finalJsonStr += '\n"' + chave + '":['
            for documento in self.tuplas[chave].tupla:
                finalJsonStr += '{'
                finalJsonStr += '"doc":"' + str(documento) + '","qt":' + str(self.tuplas[chave].tupla[documento])
                if countInner == tpls-1:
                    finalJsonStr += '}'
                else:
                    finalJsonStr += '},'
                countInner += 1
            if countOuter == chaves-1:
                finalJsonStr += ']'
            else:
                finalJsonStr += '],'

            countOuter += 1
        finalJsonStr += '}' 

        return finalJsonStr

    def fromJsonStr(self):
        with open(self.jsonPath, 'r') as jsonFile:
            indexDict = json.loads(jsonFile.read())

            for palavra in indexDict:
                for tupla in indexDict[palavra]:
                    self.addPalavra(palavra, tupla['doc'])


    def toFile(self):
        jsonTxt = self.toJsonStr()
        with open('indice.json', 'w') as arq:
            arq.write(jsonTxt)

    def printaIndices(self):
        for key, elem in self.tuplas.items():
            print('Índice: "' + key + '"')
            
    def qtdadePalavras(self):
        return len(self.tuplas)

    def listaDocsDePalavra(self, p):
        ret = []
        try:
            if self.tuplas[p]:
                for key, elem in self.tuplas[p].tupla.items():
                    ret.append(key)
        except KeyError as e:
            pass
        return ret

    def listaDocsTuplasDePalavra(self, p):
        try:
            if self.tuplas[p]:
                return self.tuplas[p]
        except KeyError as e:
            pass

    def nroDocsDePalavra(self, p): # este é o ni da fórmula
        return len(self.listaDocsDePalavra(p))
    
    #Formula TF-IDF=(1+log(fij))log(N/ni) se fij > 0
    #ou 0 se fij = 0
    def tfIdf(self, p, d):
        tfidf = 0
        listaDocsDeP = self.listaDocsTuplasDePalavra(p)
        try:
            if listaDocsDeP.tupla[d]:
                fij = listaDocsDeP.qtdadeNoDocumento(d)
                ni = self.nroDocsDePalavra(p)
                N = self.nroDocumentos
                
                if fij != 0 and ni != 0:
                    #print('N: ' + str(N) + '\nni: ' + str(ni) + '\nfij: ' + str(fij))
                    tfidf = ( 1 + math.log(fij, 10) ) * math.log(N/ni, 10)
                return tfidf
            else:
                return tfidf
        except KeyError as e:
            return tfidf
        