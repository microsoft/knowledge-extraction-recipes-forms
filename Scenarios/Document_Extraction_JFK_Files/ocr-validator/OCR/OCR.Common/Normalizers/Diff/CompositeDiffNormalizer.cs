using OCR.Common.Algorithms;
using OCR.Common.Interfaces;
using System;
using System.Collections.Generic;
using System.Text;

namespace OCR.Common.Normalizers.Diff
{
    public class CompositeDiffNormalizer : IDiffNormalizer
    {
        private readonly IEnumerable<IDiffNormalizer> normalizers;

        public CompositeDiffNormalizer()
        {
            normalizers = new List<IDiffNormalizer>() {
                new StringDistanceNormalizer(),
                new WhiteSpaceNormalizer(),
                new EqualsDiffNormalizer()
            };
        }

        public IEnumerable<Algorithms.Diff> Normalize(IEnumerable<Algorithms.Diff> input)
        {
            foreach (var formatter in normalizers)
                input = formatter.Normalize(input);
            return input;
        }
    }
}
