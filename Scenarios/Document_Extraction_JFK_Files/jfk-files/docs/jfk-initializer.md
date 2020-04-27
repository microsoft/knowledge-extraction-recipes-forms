# JFK Initializer

It's a C# console app that performs the following operations:

1. Deletes an Azure Search Data Source, Index, Indexer and Synonym map if they exist
2. Creates a Blob Storage container for storing images with public access permission. When Azure Search OCR skill extracts images from PDF documents, these images are stored in that container.
3. Creates an Azure Search data source that points to an existing JFK blob storage containing PDF files.
    > Note: The JK sample uses two Blob Storage services: a new blob storage only for storing images as described previously and an existing JFK blob storage that contains PDF documents
4. Creates an Azure Search skillset with all skills mapped.
5. Creates an Azure Search synonym map to specific names (e.g. oswold, ozwald, ozwold, oswald)
6. Creates an Azure Search index

## Skills

### Pre-built Skills

| Skill | Description |
|---------|-------------|
| OCR | Extracts printed and handwritten text from image files (.JPG)|
| Image Analysis | Detect celebrities (tags and description) |
| Text Merge | Merges native text content (text + image captions + tags) with inline OCR content where images were present |
| Text Split | Splits text into pages for subsequent skill processing |
| Language Detection  | Detect the language of input text and reports a single language code for every document submitted on the request. |
| Entity Recognition | Extract *Person*, *Localization* and *Organization* entities |
| Shaper | Custom OCR image metadata object used to generate an hOCR document, with the following metadata: layout text, image URI, width and height. |

### Custom Skills

| Skill | Description |
|---------|-------------|
| OCR Image Store | Azure Function (C#) that uploads image data to the annotation store (Blob Storage) |
| hOCR Generator | Azure Function (C#) that generates hOCR for web page rendering. For more info about what is hOCR, follow the [hOCR Generation](./hocr-generation.md) documentation. |
| Cryptonym Linker | Azure Function (C#) that links cryptonym to a description. A cryptonym is a code name used to refer to another name, often used for military purposes. Example: "AEBARMAN" = "Soviet officer Yuri Ivonovich Nosenko, who defected in Feb 1964 with information about Oswald." |

## Search index structure

| Property | Description |
|---------|-------------|
| id | The document key |
| fileName | The PDF file name (e.g. myFile.pdf) |
| metadata | The hOCR metadata |
| text | The merged content (text with image tags and splitted in pages) |
| entities | List of identified entities |
| cryptonyms | List of identified cryptonyms |
| demoBoost | Contains the search score for the item returned in search results, with range from 0 to 100 with linear interpolation (more info [here](https://docs.microsoft.com/en-us/azure/search/index-add-scoring-profiles#bkmk_interpolation)) |
