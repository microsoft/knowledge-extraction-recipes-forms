using System;
using System.Collections.Generic;
using System.Text;

namespace OCR.Common.Algorithms
{
    public class StringDistanceCalculator
    {
        public int CalculateStringDistanceBetween(string str1, string str2)
        {
            return LevenshteinDistance.CalculateDistanceBetween(str1, str2);
        }
    }
}
