using System;
using System.Collections.Generic;
using System.Text;

namespace OCR.Common.Utils
{
    public class Base64Utils
    {
        public static string Decode(string base64Encoded)
        {
            string base64WithoutPad = Repad(base64Encoded);
            string decoded = Encoding.UTF8.GetString(Convert.FromBase64String(base64WithoutPad));
            return decoded;
        }

        private static string Repad(string base64Encoded)
        {
            var length = base64Encoded.Length;
            var paddingFactor = length % 4;
            if (paddingFactor == 2)
                return base64Encoded + "==";
            if (paddingFactor == 3)
                return base64Encoded + "=";
            return base64Encoded;
        }

        public static string Encode(string value)
        {
            var encoded = Convert.ToBase64String(Encoding.UTF8.GetBytes(value));
            var base64WithoutPad = RemovePad(encoded);
            return base64WithoutPad;
        }

        private static string RemovePad(string base64Encoded)
        {
            return base64Encoded.Replace("=", "");
        }
    }
}
