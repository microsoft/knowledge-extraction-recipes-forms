# Geolocation Data

## Labeled geolocation data

In case the source data is structured with a well-defined schema, one can add geolocation data from source documents to the index to be able to query it from Azure search. Here's a [video](https://channel9.msdn.com/Shows/Data-Exposed/Azure-Search-and-Geospatial-Data) showing the possibilities of searching for entries near a given location or within a given search radius. 

Create or add a field to your index with data type Edm.GeographyPoint (see [this link](https://docs.microsoft.com/en-us/rest/api/searchservice/Supported-data-types) for supported data types). 

As an example, the [fields collection](https://docs.microsoft.com/en-us/azure/search/search-what-is-an-index#fields-collection) could contain an item:

```json
{
    "name": "my_index_geolocation",
    "type": "Edm.GeographyPoint"
  }
```



When the input data doesn't match the schema of the target index, you can use a [field mapping](https://docs.microsoft.com/en-us/azure/search/search-indexer-field-mappings) to reshape your data during the indexing process.

```json
"fieldMappings" : [
    { "sourceFieldName" : "source_geolocation", 
      "targetFieldName" : "my_index_geolocation" }
]
```



The indexer expects the representation of values to follow the GeoJSON point type format 

```json
"source_geolocation": {    
    "type": "Point",    
    "coordinates": [125.6, 10.1]   }
```



## Recognize non-labeled location data in text

If the source data is unstructured and location information is available in the content of a document -  compared to the previous case with a fixed schema - there are multiple ways to extract the information from documents or images. This mostly involves creating a [custom skill](https://docs.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-web-api) to call in order to parse the text and recognize the geolocation data. It could be as simple as parsing/searching the content of documents for a certain keyword such as "Position", "Location", "lon", "lat" and transforming it to GeoJSON format. The custom skill can be added to the [skillset](https://docs.microsoft.com/en-us/azure/search/cognitive-search-defining-skillset) to enrich the Azure Search pipepline. 

A powerful tool one could use for translating address data into geolocation information is  one of the [Azure Search Power Skills: GeoPointFromName](https://github.com/Azure-Samples/azure-search-power-skills/blob/master/Geo/GeoPointFromName/README.md). It expects a key named "address" in the input dictionary containing the location information. Azure Search has a set of [predefined skills](https://docs.microsoft.com/en-us/azure/search/cognitive-search-predefined-skills), one of which is Entity Recognition. It extracts entities of different types from text and uses the machine learning models provided by [Text Analytics](https://docs.microsoft.com/azure/cognitive-services/text-analytics/overview) in Cognitive Services. Assuming your address information has been extracted earlier in the pipeline i.e. through extracting the Entity "locations", it can be piped into the custom API by adding a custom skill. Here's an extract of the skillset containing Entity Recognition and the custom API call:

     # Extract entities
            {
              "@odata.type": "#Microsoft.Skills.Text.EntityRecognitionSkill",
              "categories": [ "Organization", "location", "person", "datetime", "url" ],
              "defaultLanguageCode": "en",
              "inputs": [
                {
                  "name": "text",
                  "source": "/document/content"
                }
              ],
              "outputs": [
                {
                  "name": "locations"
                },
                {
                  "name": "persons"
                },
                {
                  "name": "urls"
                },
                {
                  "name": "entities"
                }
              ]
            },
    # Use a custom skill to transform the location into a geolocation point 
    	 {
        	"@odata.type": "#Microsoft.Skills.Custom.WebApiSkill",
        	"description": "Geo point from name",
        	"context": "/document/content/locations/*",
        	"uri": "[AzureFunctionEndpointUrl]/api/geo-point-from-name?code=		[AzureFunctionDefaultHostKey]",
     	   "batchSize": 1,
        	"inputs": [
            	{
                "name": "address",
                "source": "/document/content/locations/*"
            	}
        	],
        	"outputs": [
            	{
                "name": "geolocation",
                "targetName": "geolocation"
            	}
        	],
        "httpHeaders": {}
    	}
Add the output for the geolocation to "outputFieldMappings" and run the indexer.

```json
    {
      "sourceFieldName" : "/document/geolocation", 
      "targetFieldName" : "my_index_geolocation"
    }
```


