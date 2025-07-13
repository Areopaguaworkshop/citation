# Introduction and goal

Citation is a tool to extract the human-readable citation information from pdf, url by using LLM.

It takes the pdf and urlas input (the input format may be extended, but right now just focus on these four), the citation information as output. It can be used by both command line and python package.

# output format
The citation information is extracted by using the LLM, and the output is in the form of a dictionary saved as yaml or json files. The citation style should be Chicago Author-data style, manily support English and Chinese. According different inputs and style, the citations information may contains the following keys with the following values:

## Pdf
### Pdf for books (over 50 pages)
- title: the title of the document (required)
- author: the author of the document (required unless editor or translator, Surname first, forname later. )
- publisher: the name of publisher (required)
- year: the publish year (required)
- location: the publish address (optional)
- editor: the editor of the document (optional, when found ed. edited by， "编"  or "主编" 等字眼出现在名字周围)
- translator: the translator of the document (optional, when found trans. or translated by, "译" or "中译" 等字眼出现在名字周围))
- volume: the volume of the document (optional)
- series: the series of the document (optional)
- isbn: the ISBN of the document ( optional)
- doi: the DOI of the document (optional)


### Pdf for thesis (over 50 pages)
- title: the title of the document (required)
- author: the author of the document (required. Surname first, forname later.)
- thesis style: Phd or Mater thesis (required. bloon)
- year: the publish year (required)
- publisher: should be a university or college (required)

### Pdf for journals (less than 50 pages)
- title: the title of the paper (required)
- author: the author of the paper (required, Surname first, forname later. )
- journal name: the name of the journal (required)
- year: the publish year (required)
- Number: the publish number of the year (required)
- page numbers: for example 20-41 means from page 20 -page 40. (required)
- isbn: the ISBN of the document ( optional)
- doi: the DOI of the document (optional)

### Pdf for book chapters (less than 50 pages)
- title: the title of the paper (required)
- author: the author of the paper (required, Surname first, forname later. )
- page numbers: for example 20-41 means from page 20 -page 40. (required)
- book name: the name of the book (required)
- publisher: the name of publisher (required)
- year: the publish year (required)
- editor: the editor of the book (optional)
- isbn: the ISBN of the document ( optional)
- doi: the DOI of the document (optional)

## Url for citations
- title: the title of the url (required)
- author: the author of the url (required, Surname first, forname later. )
- url: the url (required)
- publisher: the publisher of the document (optional)
- date: the date of the document (the date should be in the format of YYYY-MM-DD)
- date_accessed: the date of the accessed (the date should be in the format of YYYY-MM-DD)

NOTICE: For more citation information, please concern [Chicago style](https://www.chicagomanualofstyle.org/tools_citationguide/citation-guide-2.html)

## Workflow for Pdf
### First step: Using PyMupdf to check the pdf page numbers and extract the metadata and filenames. if the pages are more than 50, then it is a book or thesis, otherwise it is a journal article or or book chapter. for the metadata and filename output (if have any) transmit into next step.

### Second step:  Using refextract to check the pdf metadata and filename to see if it contains the author, title, publisher, year. Note: may using pdfx or AnyStyle as alternative. the output of this step should be title (required), author (optional), publisher(optoinal) and other information.

### Thrid step: Using scholarly library to check the output in second step, especially the title (author if it is avialable) to see the google scholar cantain other required (also include optional) infromations. If all the required information is found, then output the yaml or json file.

### Fourth step: If step 2-3 failed to find the required information, especially the title. Then write a function to check the pdf searchable or not, if not using ocrmypdf to make it searchable (if it is less 50 pages, ocr all of them; if it is more than 50 pages, only ocr first 10 pages).

### Fifth step: Then move to using dspy.lm of ollama/qwen3 model and dspy.signature for pdf books, thesis, journals and book chapters to find the citation information.
- dspy.Signature for books: ask llm to decide the the cover and copyright page, usually in first 5 pages; then ask llm in the cover page about title (usuall located in the middle and upper part with biggest fontsize) and author (usually right under the title), in the copyright page (search the publish year, and publisher)，中文也是类似的描述。
- dspy.Signature for thesis: similar like books, but focus different citation information.
- dspy.Signature for journal: ask llm to find the title (usuall located in first line with biggest fontsize) and author (usually right under the title) in the first page, the journal name, year and number in the header and footer in the first page and the page numbers usually in the footer (sometimes in header). 中文也是类似的描述。
- dspy.Signature for book chapter: ask llm to find the title (usuall located in first line with biggest fontsize) and author (usually right under the title) in the first page, the book name, year and number in the header and footer in the first page and the page numbers usually in the footer (sometimes in header). 中文也是类似的描述。

### six step. print the output and saved them as yaml or json file.

# workflow for url
### 1. check if the url is a video or audio or online article or online lecture.
### 2. if the url is a text based, using anystyle to extract the citation information.
### 3. if the url is a video or audio, using some python tools (do you have any recommendation) to extract the filename, title, lecturer, data etc. metadata information according to the [Chicago style](https://www.chicagomanualofstyle.org/tools_citationguide/citation-guide-2.html)
