using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace OCR.Validator.Web.Models
{
    public class DebugInformationViewModel
    {
        public string AzureSearchServiceName { get; set; }
        public string AzureSearchIndexName { get; set; }
        public string AzureSearchIndexerName { get; set; }
        public string AzureBlobAccountName { get; set; }
        public string AzureBlobContainerName { get; set; }
    }
}
