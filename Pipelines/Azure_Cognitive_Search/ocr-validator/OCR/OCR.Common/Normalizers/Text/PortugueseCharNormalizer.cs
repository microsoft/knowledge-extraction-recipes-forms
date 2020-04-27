using OCR.Common.Interfaces;
using System;
using System.Collections.Generic;
using System.Text;

namespace OCR.Common.Normalizers.Text
{
    public class PortugueseCharNormalizer : ITextNormalizer
    {
        private readonly Dictionary<string, string> charDictionary = new Dictionary<string, string>()
        {
            { "á", "a" },
            { "ã", "a" },
            { "â", "a" },
            { "à", "a" },
            { "é", "e" },
            { "ê", "e" },
            { "í", "i" },
            { "ó", "o" },
            { "õ", "o" },
            { "ô", "o" },
            { "ú", "u" },
            { "ç", "c" }
        };

        public string Normalize(string input)
        {
            foreach (var charPair in charDictionary)
                input = input.Replace(charPair.Key, charPair.Value);
            foreach (var charPair in charDictionary)
                input = input.Replace(charPair.Key.ToUpper(), charPair.Value.ToUpper());
            return input;
        }
    }
}
