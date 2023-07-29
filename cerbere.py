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
# * Minimal helper class for managing ip whitelist and blacklist
# *


class Cerbere:
    trials = 3
    blacklist = {}
    whitelist = {}
    suspect = {}

    # Create instance by initializing the blacklist and whitelist from the config object
    def __init__(self, config: dict):
        self.trials = config["max_tries"]
        for ip in config["blacklist"]:
            self.blacklist[ip] = True

        for ip in config["whitelist"]:
            self.whitelist[ip] = True

    # Test if an ip is blacklisted
    def blacklisted(self, ip: str) -> bool:
        return ip in self.blacklist

    # Test if an ip is whitelisted
    def whitelisted(self, ip: str) -> bool:
        return ip in self.whitelist

    # Test and ip for suspicious activity
    # and blacklit it if it exceeds the number of trials
    def watch(self, ip: str) -> bool:
        if ip not in self.whitelist:
            if not ip in self.suspect:
                self.suspect[ip] = 0

            self.suspect[ip] += 1

            if self.suspect[ip] >= self.trials:
                self.blacklist[ip] = True
                return True
