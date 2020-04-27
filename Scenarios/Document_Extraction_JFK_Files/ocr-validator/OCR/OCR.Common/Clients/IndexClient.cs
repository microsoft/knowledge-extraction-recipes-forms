using Microsoft.Azure.Search;
using Microsoft.Azure.Search.Models;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace OCR.Common.Clients
{
    public class IndexClient : IDisposable
    {
        private readonly SearchServiceClient serviceClient;
        private readonly ISearchIndexClient indexClient;

        private readonly string indexName;
        private readonly string indexerName;
        private readonly string idFieldName;

        public IndexClient(string searchServiceName, string indexName, string indexerName, string adminApiKey, string idFieldName = "Id")
        {
            this.serviceClient = new SearchServiceClient(searchServiceName, new SearchCredentials(adminApiKey));
            this.indexClient = serviceClient.Indexes.GetClient(indexName);

            this.indexName = indexName;
            this.indexerName = indexerName;
            this.idFieldName = idFieldName;
        }

        public void Dispose()
        {
            indexClient.Dispose();
            serviceClient.Dispose();
        }

        public async Task<long> GetTotalDocsCountAsync()
        {
            var parameters = new SearchParameters()
            {
                QueryType = QueryType.Full,
                IncludeTotalResultCount = true,
                Top = 0
            };
            var searchResults = await indexClient.Documents.SearchAsync("*", parameters);

            return searchResults.Count.GetValueOrDefault();
        }

        public async Task<IEnumerable<SearchResult<T>>> SearchDocumentsAsync<T>(int top, int skip, params string[] fields)
        {
            var parameters = new SearchParameters(select: fields, top: top, skip: skip);

            var search = await indexClient.Documents.SearchAsync<T>("*", parameters);

            return search.Results;
        }

        public async Task<IEnumerable<SearchResult<T>>> SearchDocumentsFilteringByFieldAsync<T>(string key, string value)
        {
            var filterQuery = string.Format("{0} eq '{1}'", key, value);
            var parameters = new SearchParameters(filter: filterQuery);

            var search = await indexClient.Documents.SearchAsync<T>("*", parameters);

            return search.Results;
        }

        public async Task IndexAsync()
        {
            await serviceClient.Indexers.RunAsync(indexerName);
        }

        public async Task DeleteEntryAsync(params string[] ids)
        {
            var batch = IndexBatch.Delete(idFieldName, ids);
            await indexClient.Documents.IndexAsync(batch);
        }

        public async Task DeleteAllAsync()
        {
            Index index = await serviceClient.Indexes.GetAsync(indexName);
            Indexer indexer = await serviceClient.Indexers.GetAsync(indexerName);

            await serviceClient.Indexes.DeleteAsync(indexName);
            await serviceClient.Indexers.DeleteAsync(indexerName);

            await serviceClient.Indexes.CreateAsync(index);
            await serviceClient.Indexers.CreateAsync(indexer);
        }

    }
}