from pyflow import Script


def _resolve(k, v):
    if isinstance(v, list):
        v = [_resolve(k, x) for x in v]
        return "/".join(v)

    if k in ["target", "source", "formula"]:
        return f'"{v}"'

    return str(v)


def _process_request(request):
    req = []
    action = request[0]
    values = request[1]
    req.append(action)
    for k, v in values.items():
        req.append("  %s=%s" % (k, _resolve(k, v)))
    req_str = ",\n".join(req)
    return req_str


class Request(Script):
    def __init__(self, requests, command="mars"):
        req = []
        if isinstance(requests, list):
            for request in requests:
                req.append(_process_request(request))
        elif isinstance(requests, tuple):
            req.append(_process_request(requests))
        req_str = "\n".join(req)
        script = f"\n{command} << EOF\n{req_str}\nEOF\n"
        super().__init__(script)


class Archive(Request):
    def __init__(self, req, command="mars", **kwargs):
        req = {**req, **kwargs}
        super().__init__(("archive", req), command=command)


class Retrieve(Request):
    def __init__(self, req, command="mars", **kwargs):
        req = {**req, **kwargs}
        super().__init__(("retrieve", req), command=command)


class Flush(Request):
    def __init__(self, req, command="mars", **kwargs):
        req = {**req, **kwargs}
        super().__init__(("flush", req), command=command)


class Stage(Request):
    def __init__(self, req, command="mars", **kwargs):
        req = {**req, **kwargs}
        super().__init__(("stage", req), command=command)


class List(Request):
    def __init__(self, req, command="mars", **kwargs):
        req = {**req, **kwargs}
        super().__init__(("list", req), command=command)
