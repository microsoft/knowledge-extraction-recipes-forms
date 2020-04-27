using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using OCR.Validator.Web.Models;
using OCR.Validator.Web.Services;

namespace OCR.Validator.Web.Controllers
{
    public class DocumentsController : Controller
    {
        private readonly DocumentsService documentsService;

        public DocumentsController(DocumentsService documentsService)
        {
            this.documentsService = documentsService;
        }

        // GET: Documents
        public async Task<IActionResult> Index()
        {
            var results = await documentsService.GetAllDocumentsAsync();
            return View(results);
        }

        // GET: Documents/Details/5
        public async Task<IActionResult> Details(string id)
        {
            DocumentDetailViewModel model = await documentsService.GetDocumentDetailAsync(id);
            return View(model);
        }

        // GET: Documents/Upload
        public IActionResult Upload()
        {
            return View();
        }

        // POST: Documents/Upload
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Upload(DocumentsUploadViewModel documents)
        {
            try
            {
                await documentsService.UploadToRepositoryAndIndexAsync(documents);

                return RedirectToAction(nameof(Index));
            }
            catch
            {
                return View();
            }
        }

        [HttpGet]
        public IActionResult Delete(string id)
        {
            return View(new DocumentViewModel() { CaseId = id });
        }

        // POST: Documents/DeleteAll
        public async Task<IActionResult> DeleteAll()
        {
            await documentsService.DeleteAllAsync();

            return RedirectToAction(nameof(Index));
        }

        // POST: Documents/Delete/5
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Delete(string id, IFormCollection collection)
        {
            try
            {
                await documentsService.DeleteAsync(id);

                return RedirectToAction(nameof(Index));
            }
            catch
            {
                return RedirectToAction(nameof(Error));
            }
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}