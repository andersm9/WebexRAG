# WebexRAG
Have a chat with a range of document types over Cisco Webex
# High Lvele Operation
## Load: 
First we will load our data. This is done with a range Document Loaders that can accept docuent in the following formats:
.pdf
.pptx
.docx
.txt
.csv
.xml
.xlsx

## Split: 
Text splitters will break the Documents into smaller chunks. This is useful both for indexing data and passing it into a model, as large chunks are harder to search over and won't fit in a model's finite context window.
## Store: 
We will store and index our splits, so that they can be searched over later. This will be done using a VectorStore and Embeddings model.
