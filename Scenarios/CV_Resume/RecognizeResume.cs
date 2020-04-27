using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Host;
using Microsoft.Extensions.Logging;
using Microsoft.Azure.CognitiveServices.Language.TextAnalytics;
using Microsoft.Azure.CognitiveServices.Language.TextAnalytics.Models;
using Microsoft.Azure.CognitiveServices.Vision.ComputerVision;
using Microsoft.Azure.CognitiveServices.Vision.ComputerVision.Models;
using Microsoft.Rest;
using iTextSharp.text.pdf;
using iTextSharp.text.pdf.parser;
using Microsoft.WindowsAzure.Storage.Blob;

namespace ResumeRecognition
{
    public static class RecognizeResume
    {
        private const string key_var = "TEXT_ANALYTICS_SUBSCRIPTION_KEY";
        private static readonly string key = Environment.GetEnvironmentVariable(key_var);

        private const string endpoint_var = "TEXT_ANALYTICS_ENDPOINT";
        private static readonly string endpoint = Environment.GetEnvironmentVariable(endpoint_var);

        private const string key_var_cv = "COMPUTER_VISION_SUBSCRIPTION_KEY";
        private static readonly string key_cv = Environment.GetEnvironmentVariable(key_var_cv);

        private const string endpoint_var_cv = "COMPUTER_VISION_ENDPOINT";
        private static readonly string endpoint_cv = Environment.GetEnvironmentVariable(endpoint_var_cv);

        private const string sas_key = "SAS";
        private static readonly string sas = Environment.GetEnvironmentVariable(sas_key);
        
        [FunctionName("RecognizeResume")]
        public static async void Run([BlobTrigger("resumes/{name}.{ext}", Connection = "ResumeStorageAccount")]Stream resumeBlob, 
        string blobTrigger, BlobProperties Properties, Uri uri, string name, string ext, ILogger log)
        {
           
            var ta_client = AuthenticateTAClient();
            var cv_client = AuthenticateCVClient(endpoint_cv,key_cv);
            if (ext.ToLower() == "pdf")
            {
                //TODO Generate SAS on the fly
                var result = await ExtractText(cv_client,uri.AbsoluteUri+sas);
                var keyPharases = ExtractkeyPhrases(result,ta_client,log);
            }
            log.LogInformation($"Blob trigger function Processed blob\n Name:{name} \n Size: {resumeBlob.Length} Bytes");
        }

        private static TextAnalyticsClient AuthenticateTAClient()
        {
            ApiKeyServiceClientCredentials credentials = new ApiKeyServiceClientCredentials(key);
            TextAnalyticsClient client = new TextAnalyticsClient(credentials)
            {
                Endpoint = endpoint
            };
            return client;
        }

        private static ComputerVisionClient AuthenticateCVClient(string endpoint, string key)
		{
			ComputerVisionClient client =
				new ComputerVisionClient(new ApiKeyServiceClientCredentials(key))
				{ Endpoint = endpoint };
			return client;
		}

        private static string keyPhrases(TextAnalyticsClient client,string textToExtract)
        {
            var result = client.KeyPhrases(textToExtract);
            string keyPhrases=string.Empty;
            Console.WriteLine("Key phrases:");

            foreach (string keyphrase in result.KeyPhrases)
            {
                Console.WriteLine($"\n{keyphrase}");
                keyPhrases+=keyphrase;
            }
            return keyPhrases;
        }

        private static string ExtractkeyPhrases (string result, TextAnalyticsClient ta_client, ILogger log) {
            string assembledContent = string.Empty;
            string keyPharases = string.Empty;
            var charCount=5000; //due to character limitation with KeyPharase extractor
 
            if (result.Length<charCount) {
                keyPharases+= keyPhrases(ta_client,result);
            }
            else {
                
                var count = result.Length/charCount;
                var remainder = result.Length%charCount;
                for (int i = 0; i < count; i++)
                {
                    assembledContent+=result.Substring(charCount*i, charCount);
                    keyPharases+= keyPhrases(ta_client,result.Substring(charCount*i, charCount));

                }
                assembledContent+= result.Substring(count*charCount);
                //check to make sure chunking is working correctly
                if (assembledContent.Equals(result)) {
                    log.LogInformation("original string and chunked+assembled strings match!");
                    keyPharases+= keyPhrases(ta_client,result.Substring(count*charCount));
                }
                else {
                    log.LogInformation("Invalid chunking. Cannot proceed");
                }

            }
            log.LogInformation(keyPharases);
            return keyPharases;
            
        }

        public static async Task<string> ExtractText(ComputerVisionClient client, string urlImage)
		{
			// Read text from URL
			BatchReadFileHeaders textHeaders = await client.BatchReadFileAsync(urlImage);
			// After the request, get the operation location (operation ID)
			string operationLocation = textHeaders.OperationLocation;

			// Retrieve the URI where the recognized text will be stored from the Operation-Location header. 
			// We only need the ID and not the full URL
			const int numberOfCharsInOperationId = 36;
			string operationId = operationLocation.Substring(operationLocation.Length - numberOfCharsInOperationId);

			// Extract the text 
			// Delay is between iterations and tries a maximum of 10 times.
			int i = 0;
			int maxRetries = 10;
			ReadOperationResult results;
			Console.WriteLine($"Extracting text from URL image {System.IO.Path.GetFileName(urlImage)}...");
			Console.WriteLine();
			do
			{
				results = await client.GetReadOperationResultAsync(operationId);
				Console.WriteLine("Server status: {0}, waiting {1} seconds...", results.Status, i);
				await Task.Delay(1000);
			}
			while ((results.Status == TextOperationStatusCodes.Running ||
					results.Status == TextOperationStatusCodes.NotStarted) && i++ < maxRetries);

			// Display the found text.
			Console.WriteLine();
			var recognitionResults = results.RecognitionResults;
            string content = string.Empty;
			foreach (TextRecognitionResult result in recognitionResults)
			{
				foreach (Microsoft.Azure.CognitiveServices.Vision.ComputerVision.Models.Line line in result.Lines)
				{
					Console.WriteLine(line.Text);
                    content+=line.Text + Environment.NewLine;
				}
			}
			Console.WriteLine();
            return content;
		}
    }
}
