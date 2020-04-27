using OCR.Common.Algorithms;
using System;
using System.Collections.Generic;
using System.Text;

namespace OCR.Common.Interfaces
{
    public interface IDiffNormalizer
    {
        IEnumerable<Diff> Normalize(IEnumerable<Diff> diff);
    }
}
