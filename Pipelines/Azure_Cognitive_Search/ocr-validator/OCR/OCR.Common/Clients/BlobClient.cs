using Microsoft.Azure.Storage;
using Microsoft.Azure.Storage.Blob;
using Polly;
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;

namespace OCR.Common.Clients
{
    public class BlobClient
    {
        private readonly CloudBlobContainer blobContainer;

        public BlobClient(string containerName, string blobConnectionString)
        {
            var storageAccount = CloudStorageAccount.Parse(blobConnectionString);
            var cloudBlobClient = storageAccount.CreateCloudBlobClient();
            this.blobContainer = cloudBlobClient.GetContainerReference(containerName);
        }

        public async Task CreateFromStreamIfNotExistsAsync(string blobName, Stream source, IDictionary<string, string> metadata)
        {
            var cloudBlockBlob = blobContainer.GetBlockBlobReference(blobName);

            if (await cloudBlockBlob.ExistsAsync())
                return;

            foreach (var m in metadata)
                cloudBlockBlob.Metadata.Add(m.Key, m.Value);

            await cloudBlockBlob.UploadFromStreamAsync(source);
        }

        public async Task DeleteAsync(params string[] blobNames)
        {
            foreach (var blobName in blobNames)
            {
                var cloudBlockBlob = blobContainer.GetBlockBlobReference(blobName);

                if (await cloudBlockBlob.ExistsAsync())
                    await cloudBlockBlob.DeleteAsync();
            }
        }

        public async Task DeleteAllAsync()
        {
            await blobContainer.DeleteAsync();

            await Policy
              .Handle<StorageException>()
              .WaitAndRetryForeverAsync(retryTentative => TimeSpan.FromSeconds(retryTentative))
              .ExecuteAsync(async () => await blobContainer.CreateAsync());
        }

        public string GetSAS(string blobName)
        {
            var cloudBlockBlob = blobContainer.GetBlockBlobReference(blobName);

            var policy = new SharedAccessBlobPolicy
            {
                SharedAccessExpiryTime = DateTime.UtcNow.AddHours(1),
                Permissions = SharedAccessBlobPermissions.Read
            };

            var sas = cloudBlockBlob.GetSharedAccessSignature(policy);

            return sas;
        }
    }
}