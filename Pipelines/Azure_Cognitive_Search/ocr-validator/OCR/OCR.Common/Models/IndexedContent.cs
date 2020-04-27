using Newtonsoft.Json;

namespace OCR.Common.Models
{
    public class IndexedContent
    {
        public string Id { get; set; }

        public string CaseId { get; set; }

        public string Role { get; set; }

        [JsonProperty("merged_content")]
        public string Content { get; set; }

        [JsonProperty("metadata_storage_path")]
        public string BlobPath { get; set; }
    }
}