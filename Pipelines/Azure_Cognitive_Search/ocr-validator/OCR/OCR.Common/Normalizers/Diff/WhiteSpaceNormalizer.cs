using OCR.Common.Algorithms;
using OCR.Common.Interfaces;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace OCR.Common.Normalizers.Diff
{
    public class WhiteSpaceNormalizer : IDiffNormalizer
    {
        public IEnumerable<Algorithms.Diff> Normalize(IEnumerable<Algorithms.Diff> diff)
        {
            return diff.Where(d => d.text.Trim().Length > 0);
        }
    }
}
