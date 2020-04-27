using Microsoft.AspNetCore.Http;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace OCR.Validator.Web.Models
{
    public class DocumentsUploadViewModel
    {
        public string CaseID { get; set; }
        public IFormFile PDFFile { get; set; }
        public IFormFile ImageFile { get; set; }
    }
}
