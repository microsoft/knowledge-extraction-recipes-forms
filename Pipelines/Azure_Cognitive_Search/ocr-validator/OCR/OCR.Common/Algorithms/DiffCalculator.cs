using System;
using System.Collections.Generic;
using System.Text;

namespace OCR.Common.Algorithms
{
    public class DiffCalculator
    {
        public IEnumerable<Diff> GetDiffBetween(string text1, string text2)
        {
            var dmp = new diff_match_patch();
            List<Diff> diff = dmp.diff_main(text1, text2);
            dmp.diff_cleanupSemantic(diff);
            return diff;
        }
    }
}
