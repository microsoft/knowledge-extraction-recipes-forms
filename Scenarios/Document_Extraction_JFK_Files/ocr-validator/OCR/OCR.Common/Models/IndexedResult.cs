using Newtonsoft.Json;
using Newtonsoft.Json.Serialization;
using System;
using System.Collections.Generic;
using System.Text;

namespace OCR.Common.Models
{
    public class IndexedResult
    {
        [JsonProperty("value")]
        public IEnumerable<Result> Values { get; set; }
    }

    public class Result
    {
        [JsonProperty("@search.score")]
        public double Score { get; set; }
        public string Id { get; set; }
    }
}
