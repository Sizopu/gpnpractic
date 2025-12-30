const express = require('express');
const https = require('https');
const fs = require('fs');

const app = express();
const port = 3000;

// Статика
const publicPath = __dirname + '/public';
app.use(express.static(publicPath));

app.get('/', (req, res) => {
    res.setHeader('Content-Type', 'text/html');
    res.sendFile(publicPath + '/index.html');
});

// Получения переменных для обработки бекенда(java)
const JAVA_HOST = process.env.JAVA_HOST || 'quotation-book-java-obs';
const JAVA_PORT = process.env.JAVA_PORT || 8443;

const HEALTH_HOST = process.env.HEALTH_HOST || 'quotation-book-dotnet-obs';
const HEALTH_PORT = process.env.HEALTH_PORT || 1443;

app.get('/api/status', async (req, res) => {
    try {
        const response = await fetch(`https://${HEALTH_HOST}:${HEALTH_PORT}/status`, {
            agent: new (require('https').Agent)({
                rejectUnauthorized: true,
                ca: fs.readFileSync('/opt/app-root/certs/sandbox_ca_root.crt')
            })
        });
        const status = await response.json();
        res.json(status);
    } catch (err) {
        console.error('Error fetching health status:', err);
        res.status(500).send('Error fetching health status');
    }
});

app.get('/api/quotes', async (req, res) => {
    try {
        const response = await fetch(`https://${JAVA_HOST}:${JAVA_PORT}/quotes`, {
            agent: new (require('https').Agent)({
                rejectUnauthorized: true,
                ca: fs.readFileSync('/opt/app-root/certs/sandbox_ca_root.crt')
            })
        });
        const quotes = await response.json();
        res.json(quotes);
    } catch (err) {
        console.error('Error fetching quotes:', err);
        res.status(500).send('Error fetching quotes');
    }
});

// Получаем метрик с java бекенда по эндопоинту /metrics
async function fetchMetrics() {
    const caCert = fs.readFileSync('/opt/app-root/certs/sandbox_ca_root.crt');

    const options = {
        hostname: JAVA_HOST,
        port: JAVA_PORT,
        path: '/metrics',
        method: 'GET',
        rejectUnauthorized: true,
        ca: caCert
    };

    return new Promise((resolve, reject) => {
        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => {
                data += chunk;
            });
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    reject(e);
                }
            });
        });

        req.on('error', (e) => {
            reject(e);
        });

        req.end();
    });
}

// Апи фронтенда для получения метрик
app.get('/api/metrics', async (req, res) => {
    try {
        const metrics = await fetchMetrics();
        res.json(metrics);
    } catch (err) {
        res.status(500).send('Error fetching metrics');
    }
});

// Запуск https сервера.
const httpsOptions = {
    key: fs.readFileSync('/opt/app-root/certs/private.key'),
    cert: fs.readFileSync('/opt/app-root/certs/certificate.crt')
};

https.createServer(httpsOptions, app).listen(port, '0.0.0.0', () => {
    console.log(`Frontend HTTPS server running at https://0.0.0.0:${port}`);
});