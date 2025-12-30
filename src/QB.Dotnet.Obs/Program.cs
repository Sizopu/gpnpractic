using System.Text.Json;
using System.Security.Cryptography.X509Certificates;

var builder = WebApplication.CreateBuilder(args);

// HTTPS
builder.WebHost.UseKestrel(kestrel =>
{
    kestrel.ListenAnyIP(1443, listenOptions =>
    {
        var cert = new X509Certificate2("/opt/app-root/certs/cert.pfx", "changeme");
        listenOptions.UseHttps(cert);
    });
});

var app = builder.Build();

// Опредяем сервисы для проверки статуса
var services = new Dictionary<string, string>
{
    { "PostgreSQL", "http://quotation-book-postgres:5432" },
    { "Java(Backend) Obs", "https://quotation-book-java-obs:8443/metrics" },
    { "Node.js frontend Obs", "https://quotation-book-javascript-obs:3000" }
};

app.MapGet("/status", async () =>
{
    var statuses = new Dictionary<string, bool>();

    foreach (var service in services)
    {
        try
        {
            using var client = new HttpClient();
            client.Timeout = TimeSpan.FromSeconds(3);
            var response = await client.GetAsync(service.Value);
            statuses[service.Key] = response.IsSuccessStatusCode;
        }
        catch
        {
            statuses[service.Key] = false;
        }
    }

    return statuses;
});



app.Run();