using System;
using System.Net.Http;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.IO;
using System.Text;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.AspNetCore.Http;
using Microsoft.Azure.WebJobs.Host;
using Newtonsoft.Json;
using System.Text.RegularExpressions;
using System.Linq;

namespace customskillfunc
{
    // This function will simply translate messages sent to it.
    public static class FunctionExtract
    {
        #region classes used to serialize the response
        private class WebApiResponseError
        {
            public string message { get; set; }
        }

        private class WebApiResponseWarning
        {
            public string message { get; set; }
        }

        private class WebApiResponseRecord
        {
            public string recordId { get; set; }
            public Dictionary<string, object> data { get; set; }
            public List<WebApiResponseError> errors { get; set; }
            public List<WebApiResponseWarning> warnings { get; set; }
        }

        private class WebApiEnricherResponse
        {
            public List<WebApiResponseRecord> values { get; set; }
        }
        #endregion

        [FunctionName("CustomListExtract")]
        public static IActionResult Run(
            [HttpTrigger(AuthorizationLevel.Function, "post", Route = null)]HttpRequest req,
            TraceWriter log)
        {
            string recordId = null;
            string originalText = null;
            List<string> productList = new List<string>();
            List<string> termList = new List<string>();

            // This is a hard list you can check in your documents
            List<string> techProducts = new List<string> { "Microsoft", "XBOX", "Windows", "Windows 10", "Windows 8", "Windows 8.1", "Office 365", "Dynamics 365", "Azure", "Cortana", "Microsoft Edge" };
            List<string> techTerms = new List<string> { "CRM", "More Personal Computing", "MPC", "AI", "Artificial Intelligence", "Machine Learning", "Deep Learning" };

            string requestBody = new StreamReader(req.Body).ReadToEnd();
            dynamic data = JsonConvert.DeserializeObject(requestBody);

            // Validation
            if (data?.values == null)
            {
                return new BadRequestObjectResult(" Could not find values array");
            }
            if (data?.values.HasValues == false || data?.values.First.HasValues == false)
            {
                // It could not find a record, then return empty values array.
                return new BadRequestObjectResult(" Could not find valid records in values array");
            }

            // Retrieve the values from json Body
            recordId = data?.values?.First?.recordId?.Value as string;
            originalText = (data?.values?.First?.data?.text?.Value as string).ToLower();

            // Search values
            termList = techTerms.Where(w => originalText.Contains(w.ToLower())).ToList<string>();
            productList = techProducts.Where(w => originalText.Contains(w.ToLower())).ToList<string>();

            if (recordId == null)
            {
                return new BadRequestObjectResult("recordId cannot be null");
            }

            // Put together response.
            WebApiResponseRecord responseRecord = new WebApiResponseRecord();
            responseRecord.data = new Dictionary<string, object>();
            responseRecord.recordId = recordId;
            responseRecord.data.Add("termList", termList);
            responseRecord.data.Add("productList", productList);
            WebApiEnricherResponse response = new WebApiEnricherResponse();
            response.values = new List<WebApiResponseRecord>();
            response.values.Add(responseRecord);

            return (ActionResult)new OkObjectResult(response);
        }


      
    }
}