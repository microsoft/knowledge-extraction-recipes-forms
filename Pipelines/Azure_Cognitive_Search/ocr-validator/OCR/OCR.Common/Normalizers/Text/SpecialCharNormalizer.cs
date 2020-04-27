using OCR.Common.Interfaces;
using System;
using System.Collections.Generic;
using System.Text;

namespace OCR.Common.Normalizers.Text
{
    public class SpecialCharNormalizer : ITextNormalizer
    {
        private readonly Dictionary<string, string> charDictionary = new Dictionary<string, string>()
        {
            { "–", "-" },
            { "\n", "" },
            { "  ", " " }
        };

        public string Normalize(string input)
        {
            foreach (var charPair in charDictionary)
                input = input.Replace(charPair.Key, charPair.Value);
            return input;
        }
    }
}
