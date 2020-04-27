using OCR.Common.Interfaces;
using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;

namespace OCR.Common.Normalizers.Text
{
    public class TagsNormalizer : ITextNormalizer
    {
        private readonly Regex imageTagRegex = new Regex(@"\[image:[a-z0-9. ]*\]", RegexOptions.Compiled);
        private readonly Regex bookmarkTagRegex = new Regex(@"\[bookmark:.*\]", RegexOptions.Compiled);

        public string Normalize(string input)
        {
            input = imageTagRegex.Replace(input, "");
            input = bookmarkTagRegex.Replace(input, "");
            return input;
        }
    }
}
