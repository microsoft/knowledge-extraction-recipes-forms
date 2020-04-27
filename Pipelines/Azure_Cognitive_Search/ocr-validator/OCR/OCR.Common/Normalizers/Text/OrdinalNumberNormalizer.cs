using OCR.Common.Interfaces;
using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;

namespace OCR.Common.Normalizers.Text
{
    public class OrdinalNumberNormalizer : ITextNormalizer
    {
        private const string resolucaoOrdinalNumberPattern = @"(Resolu[a-z]* [Nn])(o)(\ [0-9])+";
        private const string normativaOrdinalNumberPattern = @"(Normativ[a-z]* [Nn])(o)(\ [0-9])+";

        public string Normalize(string input)
        {
            input = Regex.Replace(input, resolucaoOrdinalNumberPattern, "$1°$3");
            input = Regex.Replace(input, normativaOrdinalNumberPattern, "$1°$3");

            return input;
        }

    }
}
