using Microsoft.Extensions.Configuration;
using OCR.Validator.Web.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace OCR.Validator.Web.Services
{
    public class InformationService
    {
        private readonly IConfiguration configuration;

        public InformationService(IConfiguration configuration)
        {
            this.configuration = configuration;
        }

        public DebugInformationViewModel GetDebugInformationViewModel()
        {
            return new DebugInformationViewModel()
            {
                AzureBlobAccountName = ExtractAccountNameFromConnectionString(configuration["Storage:Blob:ConnectionString"]),
                AzureBlobContainerName = configuration["Storage:Blob:ContainerName"],
                AzureSearchServiceName = configuration["Search:ServiceName"],
                AzureSearchIndexName = configuration["Search:IndexName"],
                AzureSearchIndexerName = configuration["Search:IndexerName"]
            };
        }

        private string ExtractAccountNameFromConnectionString(string connectionString)
        {
            var pieces = connectionString.Split(";");
            foreach (var piece in pieces)
            {
                var keyValue = piece.Split("=");
                var key = keyValue[0];
                var value = keyValue[1];

                if (key == "AccountName")
                    return value;
            }
            return string.Empty;
        }
    }
}
