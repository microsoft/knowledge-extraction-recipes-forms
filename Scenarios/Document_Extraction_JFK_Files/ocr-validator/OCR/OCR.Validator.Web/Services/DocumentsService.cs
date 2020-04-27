using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.Azure.Search.Models;
using OCR.Common.Algorithms;
using OCR.Common.Clients;
using OCR.Common.Interfaces;
using OCR.Common.Models;
using OCR.Common.Normalizers.Diff;
using OCR.Common.Normalizers.Text;
using OCR.Common.Utils;
using OCR.Validator.Web.Models;

namespace OCR.Validator.Web.Services
{
    public class DocumentsService
    {
        private const string CaseId = "caseId";
        private const string Role = "role";
        private const string ExpectedRole = "expected";
        private const string ActualRole = "actual";

        private readonly BlobClient blobClient;
        private readonly IndexClient indexClient;
        private readonly DiffCalculator diffCalculator;

        public DocumentsService(BlobClient blobClient, IndexClient indexClient, DiffCalculator diffCalculator)
        {
            this.blobClient = blobClient;
            this.indexClient = indexClient;
            this.diffCalculator = diffCalculator;
        }

        public async Task UploadToRepositoryAndIndexAsync(DocumentsUploadViewModel documents)
        {
            string expectedFileName = BuildFileName(documents.CaseID, documents.PDFFile);
            await UploadFileToBlobAsync(expectedFileName, documents.CaseID, ExpectedRole, documents.PDFFile);

            string actualFileName = BuildFileName(documents.CaseID, documents.ImageFile);
            await UploadFileToBlobAsync(actualFileName, documents.CaseID, ActualRole, documents.ImageFile);

            await indexClient.IndexAsync();
        }

        private static string BuildFileName(string caseId, IFormFile file)
        {
            var fileExtension = Path.GetExtension(file.FileName);
            var fileName = caseId + fileExtension;
            return fileName;
        }

        private async Task UploadFileToBlobAsync(string name, string caseId, string role, IFormFile file)
        {
            using (Stream stream = file.OpenReadStream())
            {
                await blobClient.CreateFromStreamIfNotExistsAsync(name, stream,
                    new Dictionary<string, string>() {
                        { CaseId, caseId },
                        { Role, role }
                    });
            }
        }

        public async Task<DocumentDetailViewModel> GetDocumentDetailAsync(string caseId)
        {
            var searchResults = await indexClient.SearchDocumentsFilteringByFieldAsync<IndexedContent>(CaseId, caseId);

            var expected = GetDocumentByRole(ExpectedRole, searchResults);
            string expectedContent = expected.Document.Content;

            var actual = GetDocumentByRole(ActualRole, searchResults);
            var actualContent = actual.Document.Content;

            ContentAnalysis original = GetOriginalContentAnalysis(expectedContent, actualContent);

            ContentAnalysis normalized = GetTextNormalizedContentAnalysis(expectedContent, actualContent);

            string blobPath = GetBlobPathWithAuthorization(expected);

            return new DocumentDetailViewModel()
            {
                CaseId = caseId,
                ExpectedContent = expectedContent,
                ActualContent = actualContent,
                Original = original,
                Enhanced = normalized,
                BlobPath = blobPath
            };
        }

        private SearchResult<IndexedContent> GetDocumentByRole(string role, IEnumerable<SearchResult<IndexedContent>> searchResults)
        {
            var document = searchResults.Where(s => s.Document.Role == role).First();
            return document;
        }

        private ContentAnalysis GetOriginalContentAnalysis(string expectedContent, string actualContent)
        {
            var originalDiff = diffCalculator.GetDiffBetween(expectedContent, actualContent);

            IDiffNormalizer diffNormalizer = new CompositeDiffNormalizer();
            var originalNormalizedDiff = diffNormalizer.Normalize(originalDiff);

            return new ContentAnalysis() { Diff = originalNormalizedDiff };
        }

        private ContentAnalysis GetTextNormalizedContentAnalysis(string expectedContent, string actualContent)
        {
            ITextNormalizer textNormalizer = new CompositeTextNormalizer();

            var normalizedExpectedContent = textNormalizer.Normalize(expectedContent);
            var normalizedActualContent = textNormalizer.Normalize(actualContent);

            var textNormalizedDiff = diffCalculator.GetDiffBetween(normalizedExpectedContent, normalizedActualContent);

            IDiffNormalizer diffNormalizer = new CompositeDiffNormalizer();
            var normalizedDiff = diffNormalizer.Normalize(textNormalizedDiff);

            return new ContentAnalysis() { Diff = normalizedDiff };
        }

        private string GetBlobPathWithAuthorization(SearchResult<IndexedContent> expected)
        {
            var expectedFileName = Base64Utils.Decode(expected.Document.Id);
            var sas = blobClient.GetSAS(expectedFileName);
            var blobPath = expected.Document.BlobPath + sas;

            return blobPath;
        }

        public async Task<IEnumerable<DocumentViewModel>> GetAllDocumentsAsync()
        {
            var searchResultsList = new List<SearchResult<IndexedContent>>();

            long docsCount = await indexClient.GetTotalDocsCountAsync();

            int top = 100;
            for (int skip = 0; skip < docsCount; skip += top)
            {
                var searchResults = await indexClient.SearchDocumentsAsync<IndexedContent>(top, skip, CaseId);
                searchResultsList.AddRange(searchResults);
            }

            var results = searchResultsList.Select(r => new DocumentViewModel() { CaseId = r.Document.CaseId }).Distinct();

            return results;
        }

        public async Task DeleteAllAsync()
        {
            await blobClient.DeleteAllAsync();
            await indexClient.DeleteAllAsync();
        }

        public async Task DeleteAsync(string caseId)
        {
            var searchResults = await indexClient.SearchDocumentsFilteringByFieldAsync<IndexedContent>(CaseId, caseId);

            foreach (var result in searchResults)
            {
                var blobName = Base64Utils.Decode(result.Document.Id);
                await blobClient.DeleteAsync(blobName);

                await indexClient.DeleteEntryAsync(result.Document.Id);
            }
        }
    }
}