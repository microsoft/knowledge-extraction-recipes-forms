using OCR.Common.Algorithms;
using OCR.Common.Interfaces;
using System.Collections.Generic;

namespace OCR.Common.Normalizers.Diff
{
    public class EqualsDiffNormalizer : IDiffNormalizer
    {
        public IEnumerable<Algorithms.Diff> Normalize(IEnumerable<Algorithms.Diff> diff)
        {
            List<Algorithms.Diff> normalized = new List<Algorithms.Diff>();
            Algorithms.Diff currentEquals = null;

            foreach (var d in diff)
            {
                if (d.operation == Operation.EQUAL)
                {
                    if (currentEquals != null)
                    {
                        currentEquals.text += d.text;
                    }
                    else
                    {
                        currentEquals = d;
                        normalized.Add(d);
                    }
                }
                else
                {
                    currentEquals = null;
                    normalized.Add(d);
                }
            }

            return normalized;
        }
    }
}
