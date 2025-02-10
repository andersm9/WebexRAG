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
All content for use should be placed in './Content'. All files matching the file types listed above will be detected and loaded
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

The system was tested using Python 3.12.3

## Webex setup
The solution requires a Chatbot in Webex, this can be created via: https://developer.webex.com/docs/bots. The following details are avaialble via this process for inclusion in the config/settings.toml file:

- bot_access_token       
- bot_id                   
- bot_user_name     

message_callback_url should provide the publically accesible URL of the server running the solution, with '/webexMessage' appended, e.g. a server running in AWS EC2 would take the form
"http://ec2-14-59-23-21.eu-south-1.compute.amazonaws.com/webexMessage"
This URL is used for the reciept of Webhook notifications from Webex when user messages are recieved.

