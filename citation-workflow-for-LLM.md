Instruction for LLM:
- Role: You are a code assistant, you write most of the code according to the following descriptions.
- Everytime you write code, you should understand the code, workflow and pyproject (this project is using rye as package manager.) very well.
- Everytime you write code, you should ask me some questions for more clarities. 
- You only write the code as it is necessary. You can remove the unrelated code.

# Introduction and goal

Citation is a tool to extract the human-readable citation information from pdf, url, video and audio by using LLM.

It takes the pdf, url, video and audio as input (the input format may be extended, but right now just focus on these four), the citation information as output. It can be used by both command line and python package.

# output format
The citation information is extracted by using the LLM, and the output is in the form of a dictionary saved as yaml or json files. The citation style should be Chicago Author-data style, manily support English and Chinese. According different inputs and style, the citations information may contains the following keys with the following values:

## Pdf
### Pdf for books (over 70 pages)
- title: the title of the document (required)
- author: the author of the document (required unless editor or translator, Surname first, forname later Only for English names, if it is Chinese name, leave it as is. )
- publisher: the name of publisher (required)
- year: the publish year (required)
- location: the publish address (optional)
- editor: the editor of the document (optional, when found 'ed.' 'edited by'， "编"  or "主编" 等字眼出现在名字周围)
- translator: the translator of the document (optional, when found 'trans.' or 'translated by', "译" or "中译" 等字眼出现在名字周围))
- volume: the volume of the document (optional)
- series: the series of the document (optional)
- isbn: the ISBN of the document ( optional)
- doi: the DOI of the document (optional)


### Pdf for thesis (over 70 pages)
- title: the title of the document (required)
- author: the author of the document (required unless editor or translator, Surname first, forname later Only for English names, if it is Chinese name, leave it as is. )
- thesis style: Phd or Mater thesis (required)
- year: the publish year (required)
- publisher: should be a university or college (required)

### Pdf for journals (less than 70 pages)
- title: the title of the paper (required)
- author: the author of the document (required unless editor or translator, Surname first, forname later Only for English names, if it is Chinese name, leave it as is. )
- journal name: the name of the journal (required)
- year: the publish year (required)
- Number: the publish number of the year (required)
- page_numbers: for example 20-41 means from page 20 -page 40. (required)
- isbn: the ISBN of the document ( optional)
- doi: the DOI of the document (optional)

### Pdf for book chapters (less than 50 pages)
- title: the title of the paper (required)
- author: the author of the document (required unless editor or translator, Surname first, forname later Only for English names, if it is Chinese name, leave it as is. )
- page_numbers: for example 20-41 means from page 20 -page 40. (required)
- book_name: the name of the book (required)
- publisher: the name of publisher (required)
- book_editor: the editor of the book (required)
- year: the publish year (required)
- isbn: the ISBN of the document ( optional)
- doi: the DOI of the document (optional)

## Url for citations
- title: the title of the url (required)
- author: the author of the url (required, leave the name as it is.)
- url: the url (required)
- date_accessed: the date of the accessed (required, the date should be in the format of YYYY-MM-DD)
- publisher: the publisher of the document (optional, if cann't find, using domain as publisher.)
- date: the date of the document (the date should be in the format of YYYY-MM-DD)

NOTICE: For more citation information, please concern [Chicago style](https://www.chicagomanualofstyle.org/tools_citationguide/citation-guide-2.html), looking at the website part. 

## Url for citations
- title: the title of the video (required, if cann't find, using filename as title. )
- author: the author of the url (required, leave the name as it is. if can not find, show 'missing'.)
- duration: how long the media (required)
- date_accessed: the date of the accessed (required, the date should be in the format of YYYY-MM-DD)
- publisher: the publisher of the document (optional, if cann't find, show 'missing'.)
- date: the date of the document (the date should be in the format of YYYY-MM-DD)

NOTICE: For more citation information, please concern [Chicago style](https://www.chicagomanualofstyle,.org/tools_citationguide/citation-guide-2.html), lokking at the video and podcast part. 

## Workflow for Pdf
### First step: Using PyMupdf to check the pdf page numbers and extract the metadata and filenames. if the pages are more than 70, then it is a book or thesis, otherwise it is a journal article or or book chapter.

### Second step: write a function to check the pdf searchable or not, if not using ocrmypdf to make it searchable (if it is less 70 pages, ocr all of them; if it is more than 70 pages, only ocr first 10 pages, and last two pages).

### Third step: Then move to using dspy.LM of ollama/qwen3 model and dspy.signature for pdf books, thesis, journals and book chapters to find the citation information as follow. 
#### further logic to decide which signature should be use. If the pdf is over or equal 70 pages,using Signature for books, when using the signature for books if found the key term 'thesis', 'Phd', 'Doctral', 'Instructor' in the first two pages, then turn to use the signature for thesis. 
#### if the pdf is less than 70 pages, using signature for journal as default. However, if the header didn't show any journal names and number, then switch to signature for book chapter. 
- dspy.Signature for books: ask llm to decide the the cover and copyright page, usually in first 5 pages; then ask llm in the cover page about title (usuall located in the middle and upper part with biggest fontsize) and author (usually right under the title), in the copyright page (search the publish year, and publisher)，中文也是类似的描述。
- dspy.Signature for thesis: similar like books, but find the word 'thesis' 'doctral' 'Phd' .
- dspy.Signature for journal: ask llm to find the title (usuall located in first line with biggest fontsize) and author (usually right under the title) in the first page, the journal name, year and number in the header and footer in the first page and the page numbers usually in the footer (sometimes in header). 中文也是类似的描述。
- dspy.Signature for book chapter: ask llm to find the title (usuall located in first line with biggest fontsize) and author (usually right under the title) in the first page, the book name, year and number in the header and footer in the first page and the page numbers usually in the footer (sometimes in header). 中文也是类似的描述。

### final step. print the output and saved them as yaml or json file.

## Workflow for url (wait for further instruction)
## Workflow for video and audio (wait for further instruction)
