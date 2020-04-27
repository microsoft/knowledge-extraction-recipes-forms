using System.Diagnostics;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using OCR.Validator.Web.Models;
using OCR.Validator.Web.Services;

namespace OCR.Validator.Web.Controllers
{
    public class HomeController : Controller
    {
        private readonly InformationService informationService;

        public HomeController(InformationService informationService)
        {
            this.informationService = informationService;
        }

        [HttpGet]
        public IActionResult Index()
        {
            var information = informationService.GetDebugInformationViewModel();
            return View(information);
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}
