"""
MIT License

Copyright (c) 2023 Jean-Paul Gavini

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# *
# * MooltyProxy - A simple HTTP proxy with URL mapping and body translation
# * see config.yaml for configuration details
# * Limitations:
# * - So many i can't list them all
# *

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ssl
import requests
from urllib.parse import urljoin
import os
import sys
import json
import utils
from cerbere import Cerbere
import mappers

SERVER = "MooltiProxy V1.0"
requests.packages.urllib3.util.connection.HAS_IPV6 = False


class ProxyHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.server_version = SERVER
        self.sys_version = ""
        super().__init__(*args, **kwargs)

    def do_GET(self):
        utils.info(f"Incoming GET request")
        self.proxy_request()

    def do_POST(self):
        utils.info(f"Incoming POST request")
        self.proxy_request()

    def do_OPTIONS(self):
        utils.info(f"Incoming OPTIONS request {self.path}")
        if G_debug:
            print(self.headers)

        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.send_header("access-control-allow-origin", self.headers.get("origin", "*"))
        self.send_header(
            "access-control-allow-headers",
            self.headers.get("access-control-request-headers", "*"),
        )
        self.send_header(
            "access-control-allow-methods",
            self.headers.get("access-control-request-method", "*"),
        )
        self.end_headers()

        # self.proxy_request(open=True)

    # Access denied response and log function
    def error_reply(self, code: int, payload: str, msg: str, type: str = "warning"):
        self.send_response(code)
        self.end_headers()
        self.wfile.write(bytes(json.dumps(payload), "utf-8"))
        self.wfile.flush()

        if cerbere.whitelisted(self.client_address[0]):
            msg += "\033[1;32;40m (from white-listed IP)\033[0m"

        match type:
            case "alert":
                utils.alert(msg)

            case "error":
                utils.error(msg)

            case _:
                utils.warning(msg)

    # Actual forward to target function, including url mapping and body translation
    def forward_request(self, target_config, incoming_path, open=False):
        # get the endpoint config
        endpoint_config = target_config["mapping"][incoming_path]
        # Read the request payload  and its attributes
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))
        request_body = self.rfile.read(content_length)

        # Build the target URL
        base_url = target_config["url"]
        target_url = base_url + (
            endpoint_config["path"]
            if endpoint_config and "path" in endpoint_config
            else incoming_path
        )

        utils.info(f"Forwarding to {target_url}")

        # check if we have something to do with the request body
        # else just let it pass through
        if (
            content_type == "application/json"
            and endpoint_config
            and "in" in endpoint_config
        ):
            utils.info("Mapping request body")
            # decode binary to string and load the incoming JSON data
            json_in_data = json.loads(request_body.decode("utf-8"))

            if G_debug:
                utils.debug(
                    f"Original request payload: {json.dumps(json_in_data, indent=2)}"
                )

            # get the mapping function name and the prompter function name if any
            func_name = endpoint_config["in"]
            prompt_name = (
                endpoint_config["prompt"] if "prompt" in endpoint_config else None
            )

            if prompt_name:
                utils.debug(
                    f"Mapping input with {func_name}, using prompt {prompt_name}"
                )
            else:
                utils.debug(f"Mapping input with {func_name}")

            # perform the mapping
            target_json_in_data = getattr(mappers, func_name)(json_in_data, prompt_name)

            if G_debug:
                utils.debug(
                    f"Mapped request payload: {json.dumps(target_json_in_data, indent=2)}"
                )

            # convert back to string and encode to binary
            request_body = json.dumps(target_json_in_data).encode("utf-8")

        # Build headers
        # target_headers = {}
        target_headers = {"Content-Type": self.headers.get("Content-Type", "")}
        # target_headers = dict(self.headers)

        # enrich with api key if needed
        if not open and "key" in target_config:
            target_headers.update({"Authorization": f"Bearer {target_config['key']}"})
            # target_headers["Authorization"] = f"Bearer {target_config['key']}"

        if target_config["preserveMethod"]:
            # we manually follow all redirections, while preserving th original HTTP method
            with requests.Session() as session:
                response = session.request(
                    method=self.command,
                    url=target_url,
                    headers=target_headers,
                    data=request_body,
                    stream=False,
                    allow_redirects=False,
                    timeout=(3.05, G_timeout),
                )

                while response.is_redirect:
                    redirect_url = urljoin(base_url, response.headers["location"])
                    utils.debug(f"Following redirection to {redirect_url}")
                    response = session.request(
                        method=self.command,
                        url=redirect_url,
                        headers=target_headers,
                        data=request_body,
                        allow_redirects=False,
                        timeout=(3.05, G_timeout),
                    )
        else:
            # we let the requests library handle redirections, but it will change the HTTP method to GET if needed
            response = requests.request(
                method=self.command,
                url=target_url,
                headers=target_headers,
                data=request_body,
                stream=False,
                allow_redirects=True,
                timeout=(3.05, G_timeout),
            )

        return response

    def answer_client(self, response, target_config, incoming_path):
        # get the endpoint config
        endpoint_config = target_config["mapping"][incoming_path]
        content_type = response.headers.get("Content-Type", "")

        # check if we have something to do with the response body
        # else just let it pass through
        if (
            content_type == "application/json"
            and endpoint_config
            and "out" in endpoint_config
        ):
            # get te response body as a json object
            json_out_data = response.json()

            if G_debug:
                utils.debug(
                    f"Original response payload: {json.dumps(json_out_data, indent=2)}"
                )

            # get the mapping function name
            func_name = endpoint_config["out"]
            utils.debug(f"Mapping output with {func_name}")

            # perform the mapping
            client_json_out_data = getattr(mappers, func_name)(
                json_out_data, endpoint_config
            )

            if G_debug:
                utils.debug(
                    f"Mapped response payload: {json.dumps(client_json_out_data, indent=2)}"
                )

            # convert the modified JSON data to a string
            client_response_body = json.dumps(client_json_out_data).encode("utf-8")
        else:
            client_response_body = response.content

        # Send the API response code to the client
        self.send_response(response.status_code)

        # Update the Content-Length header
        self.send_header("Content-Length", len(client_response_body))

        # list of headers to discard from the target response headers
        # either because we replace them or because they cause issues
        # todo : investigate how to handle properly
        discard = [
            "Transfer-Encoding",  # causes issues with the client
            "Content-Encoding",  # causes issues with the client
            "Content-Length",  # we replace it with the actual length of the response body (see above)
            "content-length",  # we replace it with the actual length of the response body (see above)
            "Server",  # we replace it with our own server name (automtically set by the http server)
            "Date",  # we replace it with our response time (automtically set by the http server)
        ]

        # Send the target response headers to the client (except the ones in the discard list)
        for k in response.headers:
            if k not in discard:
                # print(f"Header: {k} = {response.headers.get(k)}")
                self.send_header(k, response.headers.get(k))

        self.end_headers()

        # Send the response content to the client
        self.wfile.write(client_response_body)
        self.wfile.flush()

    def proxy_request(self, open=False):
        try:
            # if blacklisted return a 403 asap
            if cerbere.blacklisted(self.client_address[0]):
                self.error_reply(
                    403,
                    {"status": "error", "reason": "Go fuck yourself"},
                    "Blacklisted IP",
                    "alert",
                )
                return

            # if authorization is neede, but absent or incorrect, bail out wit 403
            if not open and (
                "Authorization" not in self.headers
                or self.headers["Authorization"] != f"Bearer {G_master_key}"
            ):
                self.error_reply(
                    403,
                    {"status": "error", "reason": "Access denied"},
                    "Attempt to connect with a missing or incorrect api key",
                    "warning",
                )
                # ban ip for server lifetime after too many wrong attempts
                if cerbere.watch(self.client_address[0]):
                    utils.alert("This IP is now banned till server restart")
                return

            # Get target name, using default if target header is missing
            target_name = (
                self.headers["target"]
                if "target" in self.headers
                else config["targets"]["default"]
            )

            # if target is unkwnown, 404 not found
            if not target_name in config["targets"]:
                self.error_reply(
                    404,
                    {"status": "error", "reason": "Resource not found"},
                    f"Unable to route to undefined target '{target_name}'",
                    "error",
                )
                return

            # Now we can get the target config object
            target_config = config["targets"][target_name]

            # Check if path is mapped, else bail out with 404
            incoming_path = self.path
            if incoming_path not in target_config["mapping"]:
                self.error_reply(
                    404,
                    {"status": "error", "reason": "Resource not found"},
                    f"Unable to route to unmapped incoming path '{incoming_path}'",
                    "error",
                )
                return

            # Forward the request to the target
            response = self.forward_request(target_config, incoming_path, open)

            utils.info(f"Target status code: {response.status_code}")

            if response.status_code != 200:
                self.error_reply(
                    response.status_code,
                    {"status": "error", "reason": "Target error"},
                    f"Target error: {response.status_code}",
                    "error",
                )

                utils.debug(f"Target response: {response.text}")

                return

            # send the response back to the client
            self.answer_client(response, target_config, incoming_path)

        except Exception as e:
            self.error_reply(
                500,
                {"status": "error", "reason": "Internal server error"},
                f"Internal server error: {e}",
                "error",
            )


def run(port: int):
    server_address = ("", port)
    httpd = ThreadingHTTPServer(server_address, ProxyHandler)

    # setup SSL
    if G_use_ssl:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(
            certfile="./certificates/cert.pem", keyfile="./certificates/key.pem"
        )
        httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
    utils.achievement(f"{SERVER} is running on port {port}...")
    httpd.serve_forever()


# Initialisation and launch
if __name__ == "__main__":
    utils.head(f"Starting {SERVER}...")
    utils.warning(
        "This proxy is is for experimentation only and is not intended to be used in production."
    )
    # Load configuration
    config = utils.load_config("config.yaml")

    # Get main config values
    G_port = config["system"]["port"]
    G_debug = config["system"]["debug"]
    G_use_ssl = config["system"]["ssl"]
    G_master_key = config["masterkey"]
    G_timeout = config["system"]["timeout"]

    # if G_debug:
    #     utils.debug("Configuration:\n" + json.dumps(config, indent=2))

    # Create the Cerbere instance
    cerbere = Cerbere(config["cerbere"])

    # Start the proxy server
    run(G_port)
