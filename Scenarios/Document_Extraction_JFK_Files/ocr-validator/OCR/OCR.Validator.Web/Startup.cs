using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using OCR.Common.Algorithms;
using OCR.Common.Clients;
using OCR.Validator.Web.Services;

namespace OCR.Validator.Web
{
    public class Startup
    {
        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public IConfiguration Configuration { get; }

        // This method gets called by the runtime. Use this method to add services to the container.
        public void ConfigureServices(IServiceCollection services)
        {
            services.Configure<CookiePolicyOptions>(options =>
            {
                // This lambda determines whether user consent for non-essential cookies is needed for a given request.
                options.CheckConsentNeeded = context => true;
                options.MinimumSameSitePolicy = SameSiteMode.None;
            });

            BlobClient blobClient = new BlobClient(Configuration["Azure:Storage:Blob:ContainerName"], Configuration["Azure:Storage:Blob:ConnectionString"]);
            IndexClient indexClient = new IndexClient(Configuration["Azure:Search:ServiceName"], Configuration["Azure:Search:IndexName"], Configuration["Azure:Search:IndexerName"], Configuration["Azure:Search:AdminApiKey"]);
            DiffCalculator diffService = new DiffCalculator();

            DocumentsService documentsService = new DocumentsService(blobClient, indexClient, diffService);
            services.AddSingleton<DocumentsService>(documentsService);

            InformationService informationService = new InformationService(Configuration.GetSection("Azure"));
            services.AddSingleton<InformationService>(informationService);

            services.AddMvc().SetCompatibilityVersion(CompatibilityVersion.Version_2_2);
        }

        // This method gets called by the runtime. Use this method to configure the HTTP request pipeline.
        public void Configure(IApplicationBuilder app, IHostingEnvironment env)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }
            else
            {
                app.UseExceptionHandler("/Home/Error");
            }

            app.UseStaticFiles();
            app.UseCookiePolicy();

            app.UseMvc(routes =>
            {
                routes.MapRoute(
                    name: "default",
                    template: "{controller=Home}/{action=Index}/{id?}");
            });
        }
    }
}
