using OCR.Common.Clients;
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;

namespace OCR.Ingestor
{
    class Program
    {
        static async Task Main(string[] args)
        {
            string blobConnectionString = Environment.GetEnvironmentVariable("AZURE_STORAGE_BLOB_CONNECTIONSTRING");
            string blobContainerName = Environment.GetEnvironmentVariable("AZURE_STORAGE_BLOB_CONTAINERNAME");

            BlobClient blobClient = new BlobClient(blobContainerName, blobConnectionString);
            
            string defaultPath = "C:/pdfs";
            string path = args.Length > 0 ? args[0] : defaultPath;

            var directory = new DirectoryInfo(path);
            var files = directory.GetFiles();

            foreach (var file in files)
            {
                var id = Path.GetFileNameWithoutExtension(file.Name);
                var extension = Path.GetExtension(file.Name);
                var role = extension == ".pdf" ? "expected" : "actual";

                using (Stream stream = file.OpenRead())
                {
                    await blobClient.CreateFromStreamIfNotExistsAsync(file.Name, stream,
                        new Dictionary<string, string>() {
                            { "caseId", id },
                            { "role", role }
                        });
                }
                Console.WriteLine(file.Name);
            }
        }
    }
}
