#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''

N número de documentos
ni número de documentos que contém o termo da busca
fij frequência de ocorrencia do termo Ki no doc Dj (nro de vezes que aparece em Dj)

Formula TF-IDF=(1+log(fij))log(N/ni) se fij > 0
ou 0 se fij = 0

remover radical
stemmer = nltk.stem.RSLPStemmer()
stemmer.stem('frequentemente')
stemmer.stem('copiar')

'''

from json import JSONEncoder
import sys, re, traceback, math, nltk, json, pdftotext, magic, argparse
mime = magic.Magic(mime=True)

parser = argparse.ArgumentParser()

parser.add_argument('-j', help='Arquivo json contendo objeto do indice invertido', dest='indicejsonfile', type=str)
parser.add_argument('-c', help='Consulta a ser realizada', dest='busca', type=str)
parser.add_argument('-s', help='Armazena o indice invertido em um arquivo chamado indice.json', dest='storeindice', action='store_true')

args = parser.parse_args()

if not args.busca:
    print('Input inválido')
    exit(1)

arquivo_base = 'base.txt'

nltk.download('stopwords')
stop_words = nltk.corpus.stopwords.words('portuguese')

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

'''
    A classe tupla representará a lista de documentos e quantidades
    exemplo:
    { 'documento1': 3, 'documento2': 4 }
'''
class tupla(JSONEncoder):
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

    def tupla(self):
        return self.tupla
        
'''
    A classe IndiceInvertido representará o próprio índice e cada palavra referenciará uma tupla (da classe anterior)
    exemplo:
    { 'palavra1': { 'documento1': 3, 'documento2': 4 }}
    { 'palavra2': { 'documento2': 1, 'documento3': 7 }}
'''
class IndiceInvertido(JSONEncoder):
    def __init__(self):
        self.tuplas = {}
        self.nroDocumentos = 0 # este é o N da fórmula

    def __init__(self, jsonPath=''):
        self.tuplas = {}
        self.nroDocumentos = 0 # este é o N da fórmula
        self.jsonPath = jsonPath

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
        jsonFile = open(self.jsonPath, 'r')

        indexDict = json.loads(jsonFile.read())

        for palavra in indexDict:
            for tupla in indexDict[palavra]:
                self.addPalavra(palavra, tupla['doc'])

    def toFile(self):
        jsonTxt = self.toJsonStr()
        arq = open('indice.json', 'w')
        arq.write(jsonTxt)
        arq.close()

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
                    tfidf = ( 1 + math.log(fij, 10) ) * math.log(N/ni, 10) # math.log(num, b) logarítimo de número num na base b
                return tfidf
            else:
                return tfidf
        except KeyError as e:
            return tfidf
        
    
class Busca():
    def __init__(self, ind, string_busca):
        self.indice = ind
        self.string_busca = string_busca
        self.lista_docs = []
        self.lista_docs_temp = []
        self.qtDocumentos = 0
        self.SeparaFormula()
        self.salvaRetornoArquivo()

    def SeparaFormula(self):
        b1 = self.string_busca.replace('!!', '')
        b1 = b1.split('|')
        for b in b1:
            b2 = b.split('&')
            for b22 in b2:
                palavraABuscar = b22.replace(' ', '')
                print('Palavra a buscar: ' + palavraABuscar)
                result = self.indice.listaDocsDePalavra(palavraABuscar.replace('!', '').lower())
                if result:
                    print('Result: ' + str(result))
                    if palavraABuscar[:1] == '!':
                        print('Palavra com not: ' + palavraABuscar)
                        self.lista_docs_temp = subtracao(self.lista_docs_temp, result)
                    else:
                        print('Palavra encontrada: ' + palavraABuscar)
                        if len(self.lista_docs_temp) > 0:
                            self.lista_docs_temp = interseccao(self.lista_docs_temp, result)
                        else:
                            self.lista_docs_temp = result
            self.lista_docs = uniao(self.lista_docs, self.lista_docs_temp)
            self.lista_docs_temp = []
            
    def RetornaDocumentosBusca(self):
        return self.lista_docs
    
    def salvaRetornoArquivo(self):
        self.qtDocumentos = len(self.lista_docs)
        arq = open('resposta.txt', 'w')
        arq.write(str(self.qtDocumentos) + '\n')
        for doc in self.lista_docs:
            arq.write(doc + '\n')
        arq.close()
    

def removeCaractersEspeciais(palavra):
    return palavra.lower().strip('!').replace('\n', '').replace('"', '').replace('\r', '') 

def parsearFraseInsertIndice(frase, doc, indice):
    palavrasDaFrase = re.split('[\.\? ,!]', frase) # cria vetor de strings com cada palavra separada pelos símbolos "." "?" "," e " "
    for palavra in palavrasDaFrase:
        if palavra != '' and palavra != '\n' and palavra.lower() not in stop_words:
            indice.addPalavra(removeCaractersEspeciais(palavra), doc)

def constroiIndiceInvertido(arquivoDeDocumentos):
    if args.indicejsonfile:
        indice = IndiceInvertido('indice.json')
        indice.fromJsonStr()
    else:
        indice = IndiceInvertido()
    
    try:
        arq = open(arquivoDeDocumentos, 'r')
        for d in arq.readlines():
            d = d.strip('\n')
            mimeType = magic.from_file(d, mime=True)
            if mimeType == 'text/plain':
                doc = open(d.strip('\n'), 'r')
                indice.nroDocumentos += 1
                for linha in doc.readlines():
                    parsearFraseInsertIndice(linha, d, indice)
            elif mimeType == 'application/pdf':
                with open(d, "rb") as f:
                    pdf = pdftotext.PDF(f)
                    for page in pdf:
                        parsearFraseInsertIndice(page, d, indice)
                        
                print('Finalizada leitura do pdf ' + d)


        return indice

    except Exception as e:
        print(str(e))
        traceback.print_exc() 
        exit(1)



def GeraArquivoPesos(arquivo_base, indice):
    arqDocs = open(arquivo_base, 'r')
    arqPesos = open('pesos.txt', 'w')
    
    for d in arqDocs.readlines():
        doc = d.strip('\n')
        arqPesos.write(doc + ': ')
        for p, tuplasDocs in indice.tuplas.items():
            pesoPalavraEmDoc = indice.tfIdf(p, doc)
            if pesoPalavraEmDoc != 0:
                arqPesos.write(str(pesoPalavraEmDoc) + ',')
        arqPesos.write('\n')
    
    arqPesos.close()
    arqDocs.close()

indice = constroiIndiceInvertido(arquivo_base)
GeraArquivoPesos(arquivo_base, indice)

string_busca = args.busca
  
print("String de busca: " + string_busca)    
b = Busca(indice, string_busca)

if args.storeindice:
    print("Armazenando indice invertido em arquivo")
    indice.toFile()



