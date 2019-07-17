This is a Proof of Concept of a Information Retrieval using TF-IDF Ponderation calculated over a set of documents. To run the program you must have python3 and the following dependencies:

1. nltk 
2. python-magic
3. pdftotext

You can have them by installing with the command:

`pip3 install nltk pdftotext python-magic`

The document list is defined in the file `base.txt`, you can use the `base.example` to make this file. The program will parse every document listed in `base.txt` and build the index from their contents.