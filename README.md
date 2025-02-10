# WebexRAG
Have a chat with a range of document types over Cisco Webex
# High Level Operation
## Indexing 
This happens at boot time for the solution and creates a pipeline for ingesting data from a source and indexing it
### Load: 
First we will load our data. This is done with a range Document Loaders that can accept docuent in the following formats:
- .pdf
- .pptx
- .docx
- .txt
- .csv
- .xml
- .xlsx

### Split: 
Text splitters will break the Documents into smaller chunks. This is useful both for indexing data and passing it into a model, as large chunks are harder to search over and won't fit in a model's finite context window.
### Store: 
We will store and index our splits, so that they can be searched over later. This will be done using a VectorStore and Embeddings model.

## Retrieval and generation
This is the actual RAG chain, which takes the user query (from Webex) at run time and retrieves the relevant data from the index, then passes that to the model.
### Retrieve
Taking the users input (typically a question) relevant splits are retrieved from storage using a Retriever.
### Generate
A ChatModel / LLM produces an answer using a prompt that includes both the question with the retrieved data. This project uses a privte instance of Azure ChapGPT, though other LLMs may be substituted.
