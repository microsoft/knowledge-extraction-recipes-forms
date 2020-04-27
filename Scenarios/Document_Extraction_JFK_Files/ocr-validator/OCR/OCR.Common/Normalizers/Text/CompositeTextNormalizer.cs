using OCR.Common.Interfaces;
using System;
using System.Collections.Generic;
using System.Text;

namespace OCR.Common.Normalizers.Text
{
    public class CompositeTextNormalizer : ITextNormalizer
    {
        private readonly IEnumerable<ITextNormalizer> normalizers;

        public CompositeTextNormalizer()
        {
            normalizers = new List<ITextNormalizer>() {
                new PortugueseCharNormalizer(),
                new TagsNormalizer(),
                new SpecialCharNormalizer(),
                new OrdinalNumberNormalizer()
            };
        }

        public string Normalize(string input)
        {
            foreach (var formatter in normalizers)
                input = formatter.Normalize(input);
            return input;
        }
    }
}
