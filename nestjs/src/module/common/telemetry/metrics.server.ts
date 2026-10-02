import { createServer, type Server } from "node:http";
import { metricsRegistry } from "./metrics";

export function startMetricsServer(port: number, path: string): Server {
  const server: Server = createServer((request, response) => {
    if (request.url !== path) {
      response.writeHead(404).end();
      return;
    }

    response.setHeader("Content-Type", metricsRegistry.contentType);
    void metricsRegistry
      .metrics()
      .then((body: string) => response.end(body))
      .catch(() => response.writeHead(500).end());
  });
  server.listen(port, "0.0.0.0");
  return server;
}
