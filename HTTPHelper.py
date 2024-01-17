import json
from aiohttp import web
import os
import socket
import re
import subprocess
import whois

class HTTPHelper:
    def __init__(self, worlds=[]):
        self.__file_path = "/http_request_logs.txt"

    def _get_files(self, path):
        files_dict = {}
        # Walk through all the files and subdirectories in the directory
        for root, dirs, files in os.walk(path):
            # For each file, add its name and path to the dictionary
            for file in files:
                file_path = os.path.join(root, file)
                files_dict[file] = file_path
        return files_dict

    # async def _check_query(self, path):
    #     if os.path.isfile(path):
    #         return self._get_files()
    #     else:
    #         return {"message": "no such folder"}

    async def _check_file_content(self, path):
        if os.path.isfile(path):
            with open(path, 'r') as f:
                file_contents = f.read()
            return {path: file_contents}
        elif os.path.isdir(path):
            return self._get_files(path)
        else:
            return {"message": "no such file or folder"}

    def check_ip_or_domain(self, string):
        ip_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?).){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if re.match(ip_pattern, string):
            return "ip"
        else:
            return "domain"

    def _get_ip_from_domain(self, domain_name):
        try:
            return socket.gethostbyname(domain_name)
        except:
            return "Error: Unable to get IP for domain name"

    def get_ip_info(self, ip):
        try:
            # Running the 'whois' command
            w = whois.whois(ip)
            whois_info = str(w)

            try:
                # Constructing the curl command
                curl_command = f"curl -m 5 'http://api.ipapi.com/api/{ip}?access_key=762f03e6b5ba38cff2fb5d876eb7860f&hostname=1'"
                curl_result = subprocess.run(
                    curl_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                if curl_result.returncode != 0:
                    # Curl command failed
                    self.__log(f"Curl error: {curl_result.stderr}")
                    return {"error": curl_result.stderr}

                # Parsing the response JSON
                response_json = json.loads(curl_result.stdout)
                response_json["whois"] = whois_info

                # Returning the response JSON
                return response_json

            except subprocess.CalledProcessError as e:
                self.__log(f"Curl command failed: {e}")
                return {"error": "Curl command failed"}

        except subprocess.CalledProcessError as e:
            self.__log(f"WHOIS command failed: {e}")
            return {"error": f"WHOIS command failed{e}"}

        except Exception as e:
            self.__log(f"Unexpected error: {e}")
            return {"error": "Unexpected error"}

    def __log(self, result):
        with open(self.__file_path, "a+") as f:
            f.write(result+"\n")
        if os.path.getsize(self.__file_path) > 1024*128:
            with open(self.__file_path, "r") as f:
                content = f.readlines()
                os.remove(self.__file_path)

    async def _IP_function(self, value, remote_ip):
        if value == "myself":
            return self.get_ip_info(remote_ip)
        if self.check_ip_or_domain(value) == "ip":
            return self.get_ip_info(value)
        else:
            ip = self._get_ip_from_domain(value)
            return self.get_ip_info(ip)


ROUTES = web.RouteTableDef()


def _json_response(body: dict = "", **kwargs) -> web.Response:
    kwargs["body"] = json.dumps(body or kwargs["kwargs"]).encode("utf-8")
    kwargs["content_type"] = "text/json"
    return web.Response(**kwargs)


@ROUTES.get("/lookup")
async def query_message(request: web.Request) -> web.Response:
    result = await (request.app["MANAGER"])._check_file_content(request.query["path"])
    return _json_response(result)


@ROUTES.get("/ip/{value}")
async def get_log(request: web.Request) -> web.Response:
    result = await (request.app["MANAGER"])._IP_function(request.rel_url.name, request.remote)
    return _json_response(result)


# @ROUTES.get("/{value}")
# async def query_message(request: web.Request) -> web.Response:
#     result = await (request.app["MANAGER"])._check_query(request.rel_url.name)
#     return _json_response(result)

def run():
    print("HttpRequest:1.1")
    app = web.Application()
    app.add_routes(ROUTES)
    app["MANAGER"] = HTTPHelper()
    web.run_app(app, port=7001)


if __name__ == "__main__":
    run()
