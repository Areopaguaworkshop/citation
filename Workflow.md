# Introduction and goal 

Citation is a tool to extract the human-readable citation information from pdf, url, video and audio files by using LLM. 

It takes the pdf, url, video and audio as input (the input format may be extended, but right now just focus on these four), the citation information as output. It can be used by both command line and python package.

# output format
The citation information is extracted by using the LLM, and the output is in the form of a dictionary saved as yaml files. The dictionary contains the following keys with the following values:
- title: the title of the document (if it is a book, the title should be in italics)
- author: the author of the document
- editor: the editor of the document (optional)
- translator: the translator of the document (optional)
- lecturer: the lecturer of the document (if it is a video or audio)
- chapter: the chapter of the document (optional)
- journal: the name of the journal (if it is a journal article)
- book: the name of the book (if it is a bookname with italics)
- conference: the name of the conference (optional)
- paper: the name of the paper (optional)
- thesis: the name of the thesis (optional)
- volume: the volume of the document (optional)
- edition: the edition of the document (optional)
- series: the series of the document (optional)
- pages: the number of pages of the document(optional)
- isbn: the ISBN of the document ( optional)
- doi: the DOI of the document (optional)
- url: the url of the document (optional)
- publisher: the publisher of the document (required)
- location: the location of the document (required)
- date: the date of the document (if it is url, video or audio, the date should be in the format of YYYY-MM-DD)
- date_accessed: the date of the accessed (if it is url, video or audio, the date should be in the format of YYYY-MM-DD)
- year: the year of the document (if it is not url, video or audio, required)
- url: the url of the document (if it is url)
- timeperiod: the time period of the document (if it is video or audio)
- timestamp: the timestamp of the document (if it is video or audio)
- pages: the number of pages of the document (if it is a book or articles, the number of pages should be in the format of pp. 1-10)
- type: the type of the document (pdf, url, video, audio)
- citation_type: the type of the citation (book, article, conference paper, thesis, online lecture, online article, video, audio)
- citation_style: the style of the citation (optional, default as Chicago Author-data style)

# For Pdf 

## For book with pages number more than 50 as default, extracted following informations with following order: 
Last name, First name. Year. book title. publish location: publisher name. 
    - For series books with multiple volumes, the volume number should be included in the citation.
    - For a book with an edition, the edition should be included in the citation.
    - For a book with a translator, the translator should be included in the citation.
    - For a book with an editor, the editor should be included in the citation.
    - For a book with multiple authors, the first author should be listed first, followed by the other authors in the order they appear on the title page.
    - For a book with an author and a translator, the translator should be included in the citation.
    - For a book with an author and an editor, the editor should be included in the citation.
    - For a book with multiple editors, the first author should be listed first, followed by the other authors in the order they appear on the title page.

## For a book chapter with pages number less than 50 as default, extracted following informations with following order:
Last name, First name. Year. "chapter title." in bookname, edited by editor first name last name, page number. publish location: publisher name.

## For a journal article with pages number less than 50 as default, extracted following informations with following order:
Last name, First name. Year. "article title." journal name (no.): page number. publish location: publisher name.

## For a conference paper with pages number less than 50 as default, extracted following informations with following order:
Last name, First name. Year. "paper title." in conference name, edited by editor first name last name, page number. publish location: publisher name.

## For a PhD thesis with pages number more than 50 as default, extracted following informations with following order:
Last name, First name. Year. "thesis title." PhD diss., University Name, publish location: publisher name.
    - For a PhD thesis with an advisor, the advisor should be included in the citation.
    - For a PhD thesis with a committee member, the committee member should be included in the citation.
    - For a PhD thesis with a degree, the degree should be included in the citation.
    - For a PhD thesis with a date of defense, the date of defense should be included in the citation.
## For a master thesis with pages number less than 50 as default, extracted following informations with following order:
Last name, First name. Year. "thesis title." MA thesis, University Name, publish location: publisher name.
    - For a master thesis with an advisor, the advisor should be included in the citation.
    - For a master thesis with a committee member, the committee member should be included in the citation.
    - For a master thesis with a degree, the degree should be included in the citation.
    - For a master thesis with a date of defense, the date of defense should be included in the citation.


# For url: 

## For a online lecture wither it is video or audio, extracted the lecturers, title, publisher, location and date of publish, url (if it have one), the date of accessed as its citation information. 

## For a online article, extracted the authors, title, publisher, location and date of publish, url (if it have one), the date of accessed as its citation information. 
    - For a online article with an author and a translator, the translator should be included in the citation.
    - For a online article with an author and an editor, the editor should be included in the citation.
    - For a online article with multiple authors, the first author should be listed first, followed by the other authors in the order they appear on the title page.
    - For a online article with an edition, the edition should be included in the citation.
    - For a online article with a translator, the translator should be included in the citation.
    - For a online article with an editor, the editor should be included in the citation.

# For video and audio, extracted the lecturers, title, publisher, location and date of publish, timeperiod with timestamps beginning and end,  url (if it have one), date of accessed as its citation information. 

# workflow for Pdf
## 1. check the pdf page numbers, if it is more than 50, then it is a book or thesis, otherwise it is a journal article or conference paper or book chapter.
## 2. check pdf metadata to see if it contains the author, title, publisher, location and date of publish with libraries like refextract, bibtexparser, references-parser, AnyStyle.io, and eyecite. 
## 3. if the pdf metadata is not available, then check if the pdf is ocred or not. if it is not ocred, then use marker-pdf or docling to ocr the pdf (if it is over 50 pages, only ocr first 5 pages, if it is less than 50 pages, ocr all the pages). 
## 4. using a pdf library to find the title page and copyright page in a book or thesis which over 50 pages. For academic articles of less than 50 pages, find the first page and the header or footer of the page.
## 5. if the pdf is a book or thesis, then check if it contains the author, title, publisher, location and date of publish with libraries like refextract, bibtexparser, references-parser, AnyStyle.io, and eyecite.
## 6. if the pdf is a journal article or conference paper or book chapter, then check if it contains the author, title, publisher, location and date of publish with libraries like refextract, bibtexparser, references-parser, AnyStyle.io, and eyecite.
## 7. then save it as a yaml file (or csv, json file).\

# workflow for url
## 1. check if the url is a video or audio or online article or online lecture.
## 2. if it is a video or audio, then check if it contains the lecturers, title, publisher, location and date of publish with libraries like refextract, bibtexparser, references-parser, AnyStyle.io, and eyecite.
## 3. if it is a online article, then check if it contains the authors, title, publisher, location and date of publish with libraries like refextract, bibtexparser, references-parser, AnyStyle.io, and eyecite.
## 4. if it is a online lecture, then check if it contains the lecturers, title, publisher, location and date of publish with libraries like refextract, bibtexparser, references-parser, AnyStyle.io, and eyecite.