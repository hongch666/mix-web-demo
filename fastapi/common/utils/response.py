def success(data=None, msg="success", code=1):
    return {
        "code": code,
        "data": data,
        "msg": msg
    }

def fail(msg="error", code=0, data=None):
    return {
        "code": code,
        "data": data,
        "msg": msg
    }
