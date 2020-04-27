using OCR.Common.Algorithms;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace OCR.Validator.Web.Models
{
    public class DocumentDetailViewModel
    {
        public string CaseId { get; set; }
        public string ExpectedContent { get; set; }
        public string ActualContent { get; set; }
        public string BlobPath { get; internal set; }
        public ContentAnalysis Original { get; set; }
        public ContentAnalysis Enhanced { get; set; }
    }

    public class ContentAnalysis
    {
        public IEnumerable<Diff> Diff { get; set; }
        public int CountDelete => Diff.Count(d => d.operation == Operation.DELETE);
        public int CountInsert => Diff.Count(d => d.operation == Operation.INSERT);
    }
}
