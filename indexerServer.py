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
import sys, re, traceback, nltk, json, pdftotext, magic, argparse
from unidecode import unidecode
from utils import *
from indiceInvertido import *
from flask import Flask, jsonify, request

mime = magic.Magic(mime=True)

parser = argparse.ArgumentParser()

parser.add_argument('-j', help='Arquivo json contendo objeto do indice invertido', dest='indicejsonfile', type=str)
parser.add_argument('port', help='Porta http', type=int)
parser.add_argument('-s', help='Armazena o indice invertido em um arquivo chamado indice.json', dest='storeindice', action='store_true')

args = parser.parse_args()

arquivo_base = 'base.txt'

httpServer = Flask(__name__)

nltk.download('stopwords')
stop_words = nltk.corpus.stopwords.words('portuguese')
    
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

indice = IndiceInvertido(arquivo_base, stop_words, jsonPath=args.indicejsonfile)
GeraArquivoPesos(arquivo_base, indice)

if args.storeindice:
    print("Armazenando indice invertido em arquivo")
    indice.toFile()


@httpServer.route('/consulta')
def consulta():
    global indice 
    consulta = request.args.get('consulta', '')
    print("Consulta:")
    print(consulta)
    if consulta:
        b = Busca(indice, consulta)
    else:
        return jsonify({'result': 'invalid'})

    arq = open('resposta.txt', 'r')
    content = b.lista_docs
    arq.close()

    return jsonify({'result': content})


httpServer.run(port=args.port)
