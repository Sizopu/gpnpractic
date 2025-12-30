import java.io.FileInputStream;
import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.lang.management.RuntimeMXBean;
import java.net.InetSocketAddress;
import java.security.KeyStore;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.SSLContext;

import com.sun.management.OperatingSystemMXBean;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpsServer;

public class MetricsApp {

    private static final OperatingSystemMXBean osBean =
            (com.sun.management.OperatingSystemMXBean) ManagementFactory.getOperatingSystemMXBean();
    private static final RuntimeMXBean runtimeBean = ManagementFactory.getRuntimeMXBean();
    private static final long startTime = runtimeBean.getStartTime();

    private static final String DB_HOST = System.getenv("DB_HOST");
    private static final String DB_PORT = System.getenv("DB_PORT");
    private static final String DB_NAME = System.getenv("DB_NAME");
    private static final String DB_USER = System.getenv("DB_USER");
    private static final String DB_PASSWORD = System.getenv("DB_PASSWORD");

    public static void main(String[] args) throws Exception {
        HttpsServer server = HttpsServer.create(new InetSocketAddress(8443), 0);

        SSLContext sslContext = SSLContext.getInstance("TLS");
        KeyManagerFactory kmf = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());

        KeyStore ks = KeyStore.getInstance("PKCS12");
        char[] password = "changeme".toCharArray(); // TODO: Реализовать через ENV
        ks.load(new FileInputStream("/opt/app-root/certs/keystore.p12"), password); // TODO: Реализовать через ENV
        kmf.init(ks, password);

        sslContext.init(kmf.getKeyManagers(), null, null);

        server.setHttpsConfigurator(new com.sun.net.httpserver.HttpsConfigurator(sslContext) {
            public void configure(com.sun.net.httpserver.HttpsParameters params) {
                params.setNeedClientAuth(false);
                params.setCipherSuites(null);
                params.setProtocols(null);

                javax.net.ssl.SSLParameters sslparams = sslContext.getDefaultSSLParameters();
                params.setSSLParameters(sslparams);
            }
        });

        server.createContext("/metrics", new MetricsHandler());
        server.createContext("/quotes", new QuotesHandler());
        server.setExecutor(null);
        System.out.println("HTTPS metrics server started on port 8443");
        server.start();
    }

    static class MetricsHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String response = getMetricsAsJson();

            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.getBytes().length);
            exchange.getResponseBody().write(response.getBytes());
            exchange.close();
        }

        private String getMetricsAsJson() {
            double cpuUsage = osBean.getProcessCpuLoad() * 100;
            if (Double.isNaN(cpuUsage)) {
                cpuUsage = 0.0;
            }

            long usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
            long uptimeMs = runtimeBean.getUptime();
            double uptimeSec = uptimeMs / 1000.0;

            return String.format(Locale.US,
                "{\n" +
                "  \"cpu_usage_percent\": %.2f,\n" +
                "  \"memory_used_bytes\": %d,\n" +
                "  \"uptime_seconds\": %.2f\n" +
                "}", cpuUsage, usedMemory, uptimeSec
            );
        }
    }

    static class QuotesHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String response = getQuotesAsJson();

            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.getBytes().length);
            exchange.getResponseBody().write(response.getBytes());
            exchange.close();
        }

        private String getQuotesAsJson() {
            List<String> quotes = new ArrayList<>();
            Connection conn = null;
            Statement stmt = null;
            ResultSet rs = null;

            try {
                String url = String.format("jdbc:postgresql://%s:%s/%s?sslmode=require", DB_HOST, DB_PORT, DB_NAME);
                conn = DriverManager.getConnection(url, DB_USER, DB_PASSWORD);
                stmt = conn.createStatement();
                rs = stmt.executeQuery("SELECT quote FROM quotes");

                while (rs.next()) {
                    quotes.add(rs.getString("quote"));
                }
            } catch (Exception e) {
                e.printStackTrace();
            } finally {
                try {
                    if (rs != null) rs.close();
                    if (stmt != null) stmt.close();
                    if (conn != null) conn.close();
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }

            StringBuilder json = new StringBuilder("[");
            for (int i = 0; i < quotes.size(); i++) {
                if (i > 0) json.append(",");
                json.append("\"").append(quotes.get(i).replace("\"", "\\\"")).append("\"");
            }
            json.append("]");

            return json.toString();
        }
    }
}