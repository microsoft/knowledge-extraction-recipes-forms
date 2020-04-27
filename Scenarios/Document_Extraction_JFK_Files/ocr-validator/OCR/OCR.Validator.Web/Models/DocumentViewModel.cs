using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace OCR.Validator.Web.Models
{
    public class DocumentViewModel : IEquatable<DocumentViewModel>
    {
        public string CaseId { get; set; }

        public bool Equals(DocumentViewModel other) => other.CaseId == CaseId;

        public override int GetHashCode()
        {
            return HashCode.Combine(CaseId);
        }
    }
}
