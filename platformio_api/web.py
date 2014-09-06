# Copyright (C) Ivan Kravets <me@ikravets.com>
# See LICENSE for details.

import json
from urllib import unquote

from bottle import Bottle, request, response

from platformio_api import api
from platformio_api.database import db_session
from platformio_api.exception import APIBadRequest, APINotFound


app = application = Bottle()


@app.hook("after_request")
def db_disconnet():
    db_session.close()


def finalize_json_response(handler, kwargs):
    assert issubclass(handler, api.APIBase)
    response.set_header("content-type", "application/json")

    status = 200
    error = None
    result = None
    try:
        obj = handler(**kwargs)
        result = obj.get_result()
    except APIBadRequest as error:
        status = 400
    except APINotFound as error:
        status = 404
    except Exception as error:
        status = 500

    if error:
        item = dict(
            status=status,
            title=str(error)
        )
        result = dict(errors=[item])

    response.status = status
    return json.dumps(result)


@app.route("/lib/search")
def lib_search():
    args = dict(
        query=unquote(request.query.query[:100]),
        page=int(request.query.page) if request.query.page else 0,
        per_page=int(request.query.per_page) if request.query.per_page else 0
    )
    return finalize_json_response(api.LibSearchAPI, args)


@app.route("/lib/info/<name>")
def lib_info(name):
    return finalize_json_response(api.LibInfoAPI, dict(name=name[:50]))


@app.route("/lib/download/<name>")
def lib_download(name):
    args = dict(
        name=name,
        version=request.query.version,
        ip=request.remote_addr
    )
    return finalize_json_response(api.LibDownloadAPI, args)


@app.route("/lib/version/<names>")
def lib_version(names):
    return finalize_json_response(api.LibVersionAPI,
                                  dict(names=names.split(",")))
