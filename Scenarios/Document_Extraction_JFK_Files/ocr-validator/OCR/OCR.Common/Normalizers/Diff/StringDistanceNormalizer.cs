using OCR.Common.Algorithms;
using OCR.Common.Interfaces;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace OCR.Common.Normalizers.Diff
{
    public class StringDistanceNormalizer : IDiffNormalizer
    {
        private const int MinimumWordLength = 4;
        private const double MinimumAcceptedDistanceRate = 0.10;

        public IEnumerable<Algorithms.Diff> Normalize(IEnumerable<Algorithms.Diff> diffs)
        {
            var deletes = GetDeleteOperationsWithMinimumWordLength(diffs);
            var inserts = GetInsertOperationsWithMinimumWordLength(diffs);

            var matches = ExtractMatchesUsingStringDistance(deletes, inserts);

            var normalizedList = ReplaceMatches(diffs, matches);

            return normalizedList;
        }

        private IEnumerable<Algorithms.Diff> GetDeleteOperationsWithMinimumWordLength(IEnumerable<Algorithms.Diff> diffs)
        {
            return diffs.Where(d => d.operation == Operation.DELETE && d.text.Length >= MinimumWordLength);
        }

        private IEnumerable<Algorithms.Diff> GetInsertOperationsWithMinimumWordLength(IEnumerable<Algorithms.Diff> diffs)
        {
            return diffs.Where(d => d.operation == Operation.INSERT && d.text.Length >= MinimumWordLength);
        }

        private Dictionary<Algorithms.Diff, Algorithms.Diff> ExtractMatchesUsingStringDistance(IEnumerable<Algorithms.Diff> deletes, IEnumerable<Algorithms.Diff> inserts)
        {
            var matches = new Dictionary<Algorithms.Diff, Algorithms.Diff>();

            foreach (var delete in deletes)
            {
                foreach (var insert in inserts)
                {
                    var delText = FormatStringForDistanceMetric(delete.text);
                    var insText = FormatStringForDistanceMetric(insert.text);

                    var calculator = new StringDistanceCalculator();
                    var stringDistance = calculator.CalculateStringDistanceBetween(delText, insText);

                    double averageLength = (delText.Length + insText.Length) / 2.0;
                    double stringDistanceRate = stringDistance / averageLength;

                    if (stringDistanceRate < MinimumAcceptedDistanceRate)
                    {
                        matches.Add(delete, insert);
                        break;
                    }
                }
            }

            return matches;
        }

        private string FormatStringForDistanceMetric(string text)
        {
            return text.Trim().ToLower().Replace("  ", "");
        }

        private List<Algorithms.Diff> ReplaceMatches(IEnumerable<Algorithms.Diff> diffs, Dictionary<Algorithms.Diff, Algorithms.Diff> matches)
        {
            var normalizedList = diffs.ToList();

            foreach (var match in matches)
            {
                normalizedList.Remove(match.Key);
                match.Value.operation = Operation.EQUAL;
            }

            return normalizedList;
        }
    }
}
